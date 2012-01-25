# Machine states
POWEREDOFF          = 1
SAVED               = 2
TELEPORTED          = 3
ABORTED             = 4
RUNNING             = 5
PAUSED              = 6
STUCK               = 7
TELEPORTING         = 8
LIVESNAPSHOTTING    = 9
STARTING            = 10
STOPPING            = 11
SAVING              = 12
RESTORING           = 13
TELEPORTINGPAUSEDVM = 14
TELEPORTINGIN       = 15

# Storage Bus
IDE     = 1
SATA    = 2
SCSI    = 3
Floppy  = 4
SAS     = 5

# Device Type
DT_FLOPPY       = 1
DT_DVD          = 2
DT_HARDDISK     = 3
DT_NETWORK      = 4
DT_USB          = 5
DT_SHAREDFOLDER = 6

# Access Mode
AM_RO = 0
AM_RW = 1

# Lock Type
LT_WRITE    = 0
LT_SHARED   = 1

# Cleanup Mode
CM_UNREGISTER_ONLY          = 0
CM_DETACHALL_RETURN_NONE    = 1
CM_DETACHALL_RETURN_HD_ONLY = 2
CM_FULL                     = 3