import os
import shutil
from time import sleep
from vboxapi import VirtualBoxManager

from nova.virt.vboxapi import constants
from nova import exception, flags
from nova.compute import power_state
from nova.virt import driver
from nova.image import glance



FLAGS = flags.FLAGS

flags.DEFINE_string('instances_dir',
                    '/tmp/instances',
                    'Location of installed VirtualBox machines settings and disks')

flags.DEFINE_string('default_image_format',
                    'vdi',
                    'Default image format')


VBOX_POWER_STATES = {
                   constants.POWEREDOFF: power_state.SHUTDOWN,
                    constants.RUNNING: power_state.RUNNING,
                    constants.PAUSED: power_state.PAUSED}

VALID_STATES = [constants.POWEREDOFF, constants.RUNNING, constants.PAUSED]

class VBoxVMOps(object):
    def __init__(self, read_only=False):
        self.vbox_mgr = VirtualBoxManager(None, None) # defualts to XPCOM binding style on linux
        self.vbox = self.vbox_mgr.vbox
        self.version = self.vbox.version.split(".")
        self.major_version = int(self.version[0])
        self.minor_version = int(self.version[1])
    
    def _extract_version(self, version):
        tmp = version.split('.')
        return int(tmp[0]), int(tmp[1])

    def _version_gt(self, version):
        major_version, minor_version = self._extract_version(version)
        if self.major_version > major_version:
            return True
        elif self.major_version == major_version:
            if self.minor_version > minor_version:
                return True
        return False
    
    def _version_eq(self, version):
        major_version, minor_version = self._extract_version(version)
        if major_version == self.major_version and minor_version == self.minor_version:
            return True
        return False
    
    def _version_lt(self, version):
        major_version, minor_version = self._extract_version(version)
        if self.major_version < major_version:
            return True
        elif self.major_version == major_version:
            if self.minor_version < minor_version:
                return True
        return False
    
    def _get_session(self):
        return self.vbox_mgr.mgr.getSessionObject(self.vbox)
        
    def list_instances(self):
        return [machine.id for machine in self.vbox_mgr.getArray(self.vbox, 'machines') if machine.state in VALID_STATES]

    def create_machine(self, name, os_type, settings_file=None, uuid=None, overwrite=False):
        return self.vbox.createMachine(settings_file, name, os_type, uuid, overwrite)

    def power_down(self, machine):
        session = self._get_session()
        
        # The machine is locked by a WRITE session because it's running. So we can only use a READ/SHARED session
        machine.lockMachine(session, constants.LT_SHARED)
#        try:
        progress = session.console.powerDown()
        progress.waitForCompletion(-1)
#        except:
#            # If an error occured we don't want the machine to get stuck with this locked session.
#            session.unlockMachine()
        
        # Wait until all locked sessions become unlocked.
        while machine.sessionState != 1:
            sleep(0.1)

    def delete_machine(self, machine):
        mediums_attachments = machine.getMediumAttachments()
        machine.unregister(constants.CM_FULL)
        for attachment in mediums_attachments:
            attachment.medium.close()
        dir_location = os.path.join(FLAGS.instances_dir, machine.id)
        shutil.rmtree(dir_location)

    def set_memory(self, machine, memory_size):
        machine.memorySize = memory_size

    def set_cpucount(self, machine, cpu_count):
        machine.CPUCount = cpu_count

    def open_medium(self, location, type=constants.DT_HARDDISK, access_mode=constants.AM_RW, force_new_uuid=False):
        if self._version_gt("4.0"):
            return self.vbox.openMedium(location, type, access_mode, force_new_uuid)
        else:
            return self.vbox.openMedium(location, type, access_mode)
    
    def save(self, machine, mutable=True):
        if not mutable:
            session = self._get_session()
            machine.lockMachine(session, constants.LT_WRITE)
            machine = session.machine
        
        try:
            machine.saveSettings()
        finally:
            if not mutable:
                session.unlockMachine()

    def register(self, machine):
        self.vbox.registerMachine(machine)
    
    def api_version(self):
        version = self.vbox.APIVersion
        return version.split('_')
    
    def spawn(self, context, instance, image_meta, network_info):
        try:
            self.vbox.findMachine(instance.name)
            # If findMachine didn't raise an exception then a machine with the same uuid exists.
            raise exception.InstanceExists(name=instance.name)
        except:
            machine = self._init_machine(context, instance)
            self._boot_machine(machine)
            
    def destroy(self, instance, network_info):
        try:
            machine = self.vbox.findMachine(instance.uuid)
        except:
            raise exception.InstanceNotFound(name=instance.name)

        self.power_down(machine)
        self.delete_machine(machine)
    
    def reboot(self, instance, network_info):
        try:
            machine = self.vbox.findMachine(instance.name)
        except:
            raise exception.InstanceNotFound(name=instance.name)

        session = self._get_session()
        machine.lockMachine(session, constants.LT_SHARED)
        try:
            session.console.reset()
        except:
            raise exception.InstanceRebootFailure(name=instance.name)
        finally:
            session.unlockMachine()
        
    def pause(self, instance):
        try:
            machine = self.vbox.findMachine(instance.name)
        except:
            raise exception.InstanceNotFound(name=instance.name)

        session = self._get_session()
        machine.lockMachine(session, constants.LT_SHARED)
        try:
            session.console.pause()
        except:
            raise exception.InstanceSuspendFailure(name=instance.name)
        finally:
            session.unlockMachine()
    
    def resume(self, instance):
        try:
            machine = self.vbox.findMachine(instance.name)
        except:
            raise exception.InstanceNotFound(name=instance.name)

        session = self._get_session()
        machine.lockMachine(session, constants.LT_SHARED)
        try:
            session.console.pause()
        except:
            raise exception.InstanceResumeFailure(name=instance.name)
        finally:
            session.unlockMachine()
    
    def _boot_machine(self, machine):
        session = self._get_session()
        progress = machine.launchVMProcess(session, "gui", "")
        progress.waitForCompletion(-1)
        #session.unlockMachine()
    
    def _fetch_image(self, context, instance):
        (glance_client, image_id) = glance.get_glance_client(context, instance.image_ref)
        meta_data, read_iter = glance_client.get_image(image_id)
        image_format = meta_data['properties'].get('image_format', FLAGS.default_image_format)
        disk_location = os.path.join(FLAGS.instances_dir, instance.name, "image.%s" % image_format)
        dir = os.path.dirname(disk_location)
        if not os.path.exists(dir):
            os.makedirs(dir)

        f = open(disk_location, 'wb')
        for chunk in read_iter:
            f.write(chunk)
        f.close()
            
        properties = meta_data["properties"]
        return properties
    
    def _create_machine_instance(self, instance, image_properties):
        instance_id = instance.name

        # Image info
        image_format = image_properties.get('image_format', FLAGS.default_image_format)
        
        # Hardware Information
        memory = instance.memory_mb
        cpu_count = instance.vcpus

        os_type = instance.os_type
         
        # Start building a machine from scratch.
        instance_name = instance_id
        settings_file_location = os.path.join(FLAGS.instances_dir, instance_id, "%s.vbox" % instance_id)
        machine = self.create_machine(instance_name, os_type, settings_file_location, instance_id)
        
        # Set Memory
        self.set_memory(machine, memory)
        
        # Set CPU
        self.set_cpucount(machine, cpu_count)
        
        # Using absolute pointers ( USB Tablet ) to fix the real-to-virtual mouse offset issue.
        machine.USBController.enabled = True
        machine.pointingHidType = 4
    
        # Set storage
        controller_name = instance_id
        machine.addStorageController(controller_name, constants.IDE)   

        # Always register the machine before attaching disk drives to it.
        self.register(machine)

        disk_location = os.path.join(FLAGS.instances_dir, instance_id, "image.%s" % image_format)

        session = self._get_session()
        machine.lockMachine(session, constants.LT_WRITE)
        
        medium = self.open_medium(disk_location, force_new_uuid=True)
        session.machine.attachDevice(controller_name, 0, 0, constants.DT_HARDDISK, medium)
        
        # Now that our machine is fully configured, save the settings now.
        session.machine.saveSettings()
        session.unlockMachine()
        return machine
    
    def _init_machine(self, context, instance):
        # TODO: Be a little bit nicer and create diff images for matching images.
        image_properties = self._fetch_image(context, instance)
        return self._create_machine_instance(instance, image_properties)


    def get_info(self, instance_name):
        try:
            machine = self.vbox.findMachine(instance_name)
            pwr_state = VBOX_POWER_STATES[machine.state]
            max_mem = machine.memorySize
            num_cpu = machine.CPUCount
        except:
            raise exception.InstanceNotFound(instance_id=instance_name)
        
        return {'state': pwr_state,
                    'max_mem': max_mem,
                    'mem': max_mem,
                    'num_cpu': num_cpu,
                    'cpu_time': 0}
        
    def _map_to_instance_info(self, machine):
        info = driver.InstanceInfo(machine.id, VBOX_POWER_STATES[machine.state])
        return info

    def list_instances_detail(self):
        info_list = []
        for machine in self.vbox_mgr.getArray(self.vbox, 'machines'):
            if machine.state in VALID_STATES:
                info_list.append(self._map_to_instance_info(machine))
        return info_list