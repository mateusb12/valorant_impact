from typing import List


class RoundModel:
    def __init__(self, attackers: List[str], defenders: List[str]):
        self.attackers = attackers
        self.defenders = defenders


class PlayerModel:
    def __init__(self, name: str, armor: str, acs: int, kills: int, deaths: int, damage: int, hs: float):
        self.fullshield_src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEAAQAAAAB0CZXLAAAABGdBTUEAALGPC" \
                              "/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAnRSTlMAAHaTzTgAA" \
                              "AACYktHRAAB3YoTpAAAAAlwSFlzAAAOwwAADsMBx2+oZAAAAAd0SU1FB+UCEQkOJyxg4GEAAAQJSURBVGje7" \
                              "dkxdtwgEABQeCoo1abjInnR0SAnyVV0FI5AOgo9ERAMDGJgdx3bz4VV2fCNGWAHxDLWPuvJ5s83+Ab48d5M6" \
                              "6X30ya49/MmZASTJhbv501sCZwPGvDeDoAC4Ol6UeoHTdQG6CZQA3QTvnn6+rUF7kED3ut5A30T2x0ckxjJ8" \
                              "fbd8w3eBtTL4PxksGkK8LJmFr9TIBanR4afNgrAuvQjkMdCjIGBAAy1qkUOJWaFEbi6KWfA5Y/MEBx5nocgB" \
                              "JKB/GhgKbDOgftEcA2RpXLUmkbynYCjgPxPYAuQM+CeB+IjQRoPAqQR7MCfB+AUD8AB26+5ASh3vANiBszrw" \
                              "DISnBRQJDCQzl4ASwNKtkqZcS+APwecYvARosHVp98TsNfEXsFVlYFOuT0BKMAAcvebQd5EVgqwO9DPAzYDr" \
                              "AV+DDS7R6E5BfTbgBqDEwH1FECdZBOwDsFZNtIGbGV5HLCXR7CUggps2asHQLPaSwqUM4WgwIYOocsAlGMsb4EEAH2MvUwfRvc8MD0QBaxjYEtQ5t7JMxdDUNfmjcM8ywEkBWWaNywBQJehNzkWBiOTQP09ATRZF4D/KQGg6b6yN/R6LZt3nasjlZaCBqwATI0qA90C6DQrm3dd9hcoI6toUA+lGw3qW4ykQX0PWlsAnayzu8DmXcN010G2Ti8J4FPAQ8ZrgMiALYnwsHfkzbsBYb4yCJssBUI/MwjtZ6BxH8LwZxDaokD4zxmE3mSwl4EKIPQdgOZ5dzewwgLYQpaCNbmzDNyvMGo6pYotjB/MtmE/4XygmfzrLxCLADj2AzZO2BZtKJIFHIz1IPYFwMnQzYEqQAG4fiBAWVIqhpMBHA9sDL8CQwGBgC0AjiiWoVWr4urjLTBxxAFsMc5ccZTOpuIMTgooBEIYGcBRzcQCBPZyBPEAlgaYHogG2B6sTYZxPZA1w6QE14Jrf0DA98C/J1hHwL4C9B3w14F6DWgMxAiYZ8EyApDm+AhAmmMjAPWx7n49oBd8wyD7l/sIcK4mgS2AuB6oVwM5TgrsBXAalChjGATA1yQbBfC9muze3UPH8c3cSgGLgKCAQYBTAAVxZeMGnDUP5zh70N4WbT1obw/XHtgGiNu7+xn/BD9LD/YG8B40UTLWA3Z/GnAw9joQj8CCgSNAkygNAZoMslNAIaApgBclVY9ni75WR3EeJEBxOhKgOC0JUJyGBjXOnQY1Tk2DGiddXyd89O2CmEf5xLcP/EGUdSD2EVDzKGuco3qIc/w1jJhNNorTDQGfD0OJ04yBmg8DTPi4/uGXTWkgjgkQ8yjzQEyiTHGaGVDzKFOcegbkfBiuOOff/In5MFxxuingD4YhXfJPn20e5df4hvQbfGHwD5eRMRZBXdhhAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDIxLTAyLTE3VDA5OjE0OjM5KzAwOjAwQbgAlwAAACV0RVh0ZGF0ZTptb2RpZnkAMjAyMS0wMi0xN1QwOToxNDozOSswMDowMDDluCsAAAAASUVORK5CYII= "


