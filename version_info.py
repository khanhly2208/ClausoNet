# UTF-8
# ClausoNet 4.0 Pro - Version Information for Windows EXE
# Sử dụng với PyInstaller để embed version info vào EXE

# Import required for version_info
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable,
    StringStruct, VarFileInfo, VarStruct
)

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(4, 0, 0, 1),
        prodvers=(4, 0, 0, 1),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    u'040904B0',
                    [
                        StringStruct(u'CompanyName', u'ClausoNet Technologies'),
                        StringStruct(u'FileDescription', u'ClausoNet 4.0 Pro - AI Video Generation Tool'),
                        StringStruct(u'FileVersion', u'4.0.0.1'),
                        StringStruct(u'InternalName', u'ClausoNet4.0Pro'),
                        StringStruct(u'LegalCopyright', u'Copyright © 2025 ClausoNet Technologies'),
                        StringStruct(u'OriginalFilename', u'ClausoNet4.0Pro.exe'),
                        StringStruct(u'ProductName', u'ClausoNet 4.0 Pro'),
                        StringStruct(u'ProductVersion', u'4.0.0.1'),
                        StringStruct(u'Comments', u'Professional AI Video Generation and Automation Tool'),
                        StringStruct(u'LegalTrademarks', u'ClausoNet™'),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
    ]
)
