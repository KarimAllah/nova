# vim: tabstop=4 shiftwidth=4 softtabstop=4
from nova.virt.vboxapi.vmops import VBoxVMOps

# Copyright 2011 OpenStack LLC.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
A connection to the VirtualBox.

"""

from eventlet import event
from nova import log as logging
from nova.virt import driver


LOG = logging.getLogger("nova.virt.vboxapi_conn")


class Failure(Exception):
    """Base Exception class for handling task failures."""

    def __init__(self, details):
        self.details = details

    def __str__(self):
        return str(self.details)


def get_connection(read_only = False):
    """Sets up the VBoxAPI connection."""
    return VBoxConnection(read_only)

class VBoxConnection(driver.ComputeDriver):
    """The VBox connection object."""
    def __init__(self, read_only):
        super(VBoxConnection, self).__init__()
        self.host_status = {
          'host_name-description': 'VBox Host',
          'host_hostname': 'fake-mini',
          'host_memory_total': 8000000000,
          'host_memory_overhead': 10000000,
          'host_memory_free': 7900000000,
          'host_memory_free_computed': 7900000000,
          'host_other_config': {},
          'host_ip_address': '127.0.0.1',
          'host_cpu_info': {},
          'disk_available': 500000000000,
          'disk_total': 600000000000,
          'disk_used': 100000000000,
          'host_uuid': 'cedb9b39-9388-41df-8891-c5c9a0c0fe5f',
          'host_name_label': 'fake-mini'}

        self._vmops = VBoxVMOps(read_only)

    def init_host(self, host):
        """Do the initialization that needs to be done."""
        # FIXME(sateesh): implement this
        pass

    def list_instances(self):
        """List VM instances."""
        return self._vmops.list_instances()

    def spawn(self, context, instance, image_meta, network_info,
              block_device_mapping=None):
        """Create VM instance."""
        self._vmops.spawn(context, instance, image_meta, network_info)
        
    def update_host_status(self):
        """Return fake Host Status of ram, disk, network."""
        return self.host_status
    
    def get_host_stats(self, refresh=False):
        """Return fake Host Status of ram, disk, network."""
        return self.host_status
    
    def list_instances_detail(self):
        return self._vmops.list_instances_detail()
#
#    def snapshot(self, context, instance, name):
#        """Create snapshot from a running VM instance."""
#        self._vmops.snapshot(context, instance, name)
#
    def reboot(self, instance, network_info, reboot_type):
        """Reboot VM instance."""
        self._vmops.reboot(instance, network_info)
#
    def destroy(self, instance, network_info, block_device_info=None):
        """Destroy VM instance."""
        self._vmops.destroy(instance, network_info)

    def pause(self, instance):
        """Pause VM instance."""
        self._vmops.pause(instance)

    def unpause(self, instance):
        """Unpause paused VM instance."""
        self._vmops.unpause(instance)
#
#    def suspend(self, instance):
#        """Suspend the specified instance."""
#        self._vmops.suspend(instance)
#
#    def resume(self, instance):
#        """Resume the suspended VM instance."""
#        self._vmops.resume(instance)
#
    def get_info(self, instance_name):
        """Return info about the VM instance."""
        return self._vmops.get_info(instance_name)
#
#    def get_diagnostics(self, instance):
#        """Return data about VM diagnostics."""
#        return self._vmops.get_info(instance)
#
#    def get_console_output(self, instance):
#        """Return snapshot of console."""
#        return self._vmops.get_console_output(instance)
#
#    def get_ajax_console(self, instance):
#        """Return link to instance's ajax console."""
#        return self._vmops.get_ajax_console(instance)
#
#    def attach_volume(self, connection_info, instance_name, mountpoint):
#        """Attach volume storage to VM instance."""
#        pass
#
#    def detach_volume(self, connection_info, instance_name, mountpoint):
#        """Detach volume storage to VM instance."""
#        pass
#
#    def get_console_pool_info(self, console_type):
#        """Get info about the host on which the VM resides."""
#        return {'address': FLAGS.vmwareapi_host_ip,
#                'username': FLAGS.vmwareapi_host_username,
#                'password': FLAGS.vmwareapi_host_password}
#
    def update_available_resource(self, ctxt, host):
        """This method is supported only by libvirt."""
        return
#
#    def host_power_action(self, host, action):
#        """Reboots, shuts down or powers up the host."""
#        pass
#
#    def set_host_enabled(self, host, enabled):
#        """Sets the specified host's ability to accept new instances."""
#        pass
#
#    def plug_vifs(self, instance, network_info):
#        """Plug VIFs into networks."""
#        self._vmops.plug_vifs(instance, network_info)
#
#    def unplug_vifs(self, instance, network_info):
#        """Unplug VIFs from networks."""
#        self._vmops.unplug_vifs(instance, network_info)