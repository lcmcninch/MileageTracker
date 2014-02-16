# -*- mode: python -*-
a = Analysis(['main.py'],
             pathex=['C:\\Users\\Luke\\Desktop\\PyinstallerTest'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
a.datas += [('icons\\gas-station-multi-size.ico', r'icons\gas-station-multi-size.ico', 'DATA'),
            ('icons\\splash_loading.png', r'icons\splash_loading.png', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='MileageTracker.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon=r'icons\gas-station-multi-size.ico')
