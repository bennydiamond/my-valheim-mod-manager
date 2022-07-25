import secreturls
import os
import shutil
import argparse
import hashlib
import configparser
import winreg
import vdf
import requests
from tqdm.auto import tqdm
from consolemenu import *
from consolemenu.items import *

Version = "0.1"

RegistrySteamPath = "SOFTWARE\\Valve\\Steam"
RegistrySteamSubKeyName = "SteamPath"

SteamVDFSubPath = "\\steamapps\\libraryfolders.vdf"
SteamAppIDValheim = '892970'
SteamValheimInstallSubpath = "\\steamapps\\common\\Valheim"

ValheimExePath = "valheim.exe"

ModFolderPath = "BepInEx"

ManifestFile = "modpack.manifest"
DefaultHashesFilepath = "mod_hashes.properties"

ExtraModFilesFolderPath = "Extra_Mods_Backup"

MustMoveExtraFiles = True
SilentCheckMD5 = True

ValheimVRConfigPath = "BepInEx\\config\\org.bepinex.plugins.valheimvrmod.cfg"
ValheimVRNonVRCategoryName = "Immutable"
ValheimVRNonVREntryName = "nonVrPlayer"

AugaConfigPath = "BepInEx\\config\\randyknapp.mods.auga.cfg"
AugaVRCategoryName = "Options"
AugaVRModeConfigEntryName = "UseAugaVR"

valheimVRConfig = configparser.ConfigParser()
augaVRConfig = configparser.ConfigParser()

HashExcludeFolders = [
                        'BepInEx\\cache',
                        'BepInEx\\Debug',
                        'BepInEx\\vplus-data'
                     ]
HashExcludeList = [
                    'BepInEx\\LogOutput.log',
                    'BepInEx\\plugins\\MultiUserChest-log.txt'
                  ]

def fmove(src,dest):
    """
    Move file from source to dest.  dest can include an absolute or relative path
    If the path doesn't exist, it gets created
    """
    dest_dir = os.path.dirname(dest)
    try:
        os.makedirs(dest_dir)
    except os.error as e:
        pass #Assume it exists.  This could fail if you don't have permissions, etc...
    shutil.move(src,dest)
    remove_empty_folders(os.path.dirname(src))
    return
    
def remove_empty_folders(path_abs):
    '''
    Remove folder when empty
    '''
    walk = list(os.walk(path_abs))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            shutil.rmtree(path)
    return

def validateModInstall():
    '''
    Validate if in the same dir as valheim.exe
    '''
    file_exists = os.path.exists(ValheimExePath)
    '''
    valheimVRConfig.read(ValheimVRConfigPath)
    augaVRConfig.read(AugaConfigPath)
    file_exists &= valheimVRConfig.has_option(ValheimVRNonVRCategoryName, ValheimVRNonVREntryName)
    file_exists &= augaVRConfig.has_option(AugaVRCategoryName, AugaVRModeConfigEntryName)
    '''
    return file_exists

def isVRActive():
    '''
    Return true if 2 config files are set to VR mode ON
    '''
    return valheimVRConfig.getboolean(ValheimVRNonVRCategoryName ,ValheimVRNonVREntryName) is False and augaVRConfig.getboolean(AugaVRCategoryName, AugaVRModeConfigEntryName) is True

def isVRDisabled():
    return valheimVRConfig.getboolean(ValheimVRNonVRCategoryName, ValheimVRNonVREntryName) is True and augaVRConfig.getboolean(AugaVRCategoryName, AugaVRModeConfigEntryName) is False

def enableVRMode():
    valheimVRConfig[ValheimVRNonVRCategoryName][ValheimVRNonVREntryName] = "false"
    augaVRConfig[AugaVRCategoryName][AugaVRModeConfigEntryName] = "true"
    with open(ValheimVRConfigPath, 'w') as configfile:    # save
        valheimVRConfig.write(configfile)
        configfile.close()
    with open(AugaConfigPath, 'w') as configfile:    # save
        augaVRConfig.write(configfile)
        configfile.close()
    return

def disableVRMode():
    valheimVRConfig[ValheimVRNonVRCategoryName][ValheimVRNonVREntryName] = "true"
    augaVRConfig[AugaVRCategoryName][AugaVRModeConfigEntryName] = "false"
    with open(ValheimVRConfigPath, 'w') as configfile:    # save
        valheimVRConfig.write(configfile)
        configfile.close()
    with open(AugaConfigPath, 'w') as configfile:    # save
        augaVRConfig.write(configfile)
        configfile.close()
    return

def generateMD5list(exePath):
    '''
    Generates a file of all the filenames of files related to mods
    Appends matching MD5 sum
    Useful for when updating a modpack with new mods versions
    Generates
    '''
    hashesConfig = configparser.ConfigParser()
    hashesConfig.optionxform = str # Preserve capitalization
    hashes = open(os.path.join(exePath, DefaultHashesFilepath), 'w')
    for root, subdirs, files in os.walk(ModFolderPath):
        if root not in HashExcludeFolders: # Exclude whole folders
            for file in files:
                if os.path.join(root, file) not in HashExcludeList: # Exclude specific files
                    if not hashesConfig.has_section(root):
                        hashesConfig.add_section(root)
                    if os.path.join(root, file) == ValheimVRConfigPath:
                        enableVRMode()
                        multihash1 = str()
                        with open(os.path.join(root, file), 'rb') as _file:
                            multihash1 = str(hashlib.md5(_file.read()).hexdigest())
                        multihash1 += ','
                        disableVRMode()
                        with open(os.path.join(root, file), 'rb') as _file:
                            multihash1 += str(hashlib.md5(_file.read()).hexdigest())
                        hashesConfig.set(root, file, multihash1)
                    elif os.path.join(root, file) == AugaConfigPath:
                        enableVRMode()
                        multihash1
                        with open(os.path.join(root, file), 'rb') as _file:
                            multihash1 = str(hashlib.md5(_file.read()).hexdigest())
                        multihash1 += ','
                        disableVRMode()
                        with open(os.path.join(root, file), 'rb') as _file:
                            multihash1 += str(hashlib.md5(_file.read()).hexdigest())
                        hashesConfig.set(root, file, multihash1)
                    else:
                        with open(os.path.join(root, file), 'rb') as _file:
                            hashesConfig.set(root, file, str(hashlib.md5(_file.read()).hexdigest()))        
    hashesConfig.write(hashes)
    hashes.close()
    return

def checkMD5(HashesFilepath, mustMoveExtraFiles, silent):
    hashesConfig = configparser.ConfigParser()
    hashesConfig.optionxform = str # Preserve capitalization
    hashesConfig.read(HashesFilepath)
    hashesList = []
    extraModFiles = []
    for root, subdirs, files in os.walk(ModFolderPath):
        if root not in HashExcludeFolders: # Exclude whole folders
            for file in files:
                if os.path.join(root, file) not in HashExcludeList: # Exclude specific files
                    if hashesConfig.has_option(root, file):
                        with open(os.path.join(root, file), 'rb') as _file:
                            dictEntry = os.path.join(root, file), str(hashlib.md5(_file.read()).hexdigest())
                            hashesList.append(dictEntry)
                    else:
                        extraModFiles.append(os.path.join(root, file))

    hashesList = dict(hashesList)

    if mustMoveExtraFiles is True and extraModFiles:
        print("\r\nAttention! Il y a des fichiers de mods en trop dans votre installation de Valheim.")
        print("Liste des fichiers en trop:")
        print(*extraModFiles, sep = "\r\n")
        for file in extraModFiles:
            fmove(file, os.path.join(ExtraModFilesFolderPath, file))
        print("Les fichiers superflus ont été déplacé dans le dossier " + os.path.join(os.path.abspath(os.getcwd()), ExtraModFilesFolderPath))

    missingMods = []
    wrongHashList = []
    for section in hashesConfig.sections():
        for (filename, hash) in hashesConfig.items(section):
            try:
                if not hashesList[os.path.join(section, filename)]:
                    missingMods.append(os.path.join(section, filename))
                else:
                    if hashesList[os.path.join(section, filename)] not in hashesConfig[section][filename].split(','):
                        wrongHashList.append(os.path.join(section, filename))
            except Exception: 
                pass

    if silent is False and missingMods:
        print("\r\nErreur! Il manque les mods suivants dans votre installation de Valheim.\r\nLa connection au serveur pourrait être refusée!")
        print(*missingMods, sep = "\r\n")

    if silent is False and wrongHashList:
        print("\r\nErreur. Les mods suivants sont corrompes dans votre installation de Valheim.\r\nLa connection au serveur pourrait être refusée!")
        print(*wrongHashList, sep = "\r\n")

    return not missingMods and not wrongHashList

def installModpack(manifest, hashesFilepath):
    '''
    Delete any exsiting modpack zip and download a new copy
    Extract with directory structure in basedir
    '''

    zipFilePath = manifest['Modpack']['filename'].lower()
    zipFileUrl = manifest['Modpack']['url']
    zipFileMd5 = manifest['Modpack']['md5'].lower()
    if not os.path.exists(zipFilePath):
        downloadFile(zipFileUrl, zipFilePath)
    loop = 0
    while loop <= 1:
        with open(zipFilePath, 'rb') as _file:
            computedModpackMd5 = str(hashlib.md5(_file.read()).hexdigest())
            if computedModpackMd5 != zipFileMd5:
                downloadFile(zipFileUrl, zipFilePath)
            else:
                loop = 2
        loop += 1

    # TODO Download file from http server
    # TODO unzip in proper location
    checkMD5(hashesFilepath, MustMoveExtraFiles, SilentCheckMD5)


    import zipfile
    with zipfile.ZipFile(zipFilePath,"r") as zip_ref:
        zip_ref.extractall()

    return

def checkManagerVersion(manifest):
    cdnVersion = manifest['DEFAULT']['version']
    
    return cdnVersion == Version

def checkHashesListFileAndDownloadIfRequired(manifest):
    '''
    Check if hashes list is up to date
    Download a copy if necessary
    TODO error handling
    '''
    hashesFilepath = DefaultHashesFilepath

    hashesFilepath = manifest['Hashes']['filename'].lower()
    hashesUrl = manifest['Hashes']['url']
    hashesFileMd5 = manifest['Hashes']['md5'].lower()

    if not os.path.exists(hashesFilepath):
        downloadFile(hashesUrl, hashesFilepath)
    loop = 0
    while loop <= 1:
        with open(hashesFilepath, 'rb') as _file:
            computedHashesListMd5 = str(hashlib.md5(_file.read()).hexdigest())
            if computedHashesListMd5 != hashesFileMd5:
                downloadFile(hashesUrl, hashesFilepath)
            else:
                loop = 2
        loop += 1

    return hashesFilepath

def downloadFile(url, filename):
    '''
    Fetch and store a file from server
    Overwrites already present file if there
    TODO error handling
    '''
    result = False
    chunk_size = 1024

    print("Téléchargement du fichier: " + filename)

    response = requests.get(url, stream=True, allow_redirects=True)
    assert response.status_code == 200, response.status_code
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("Erreur de téléchargement pour le fichier " + filename)
    else:
        result =  True

    return result

def findSteamInstall():
    try:
        aReg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    except OSError as e:
        aReg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    aKey = winreg.OpenKey(aReg, RegistrySteamPath)
    installPath, valType = winreg.QueryValueEx(aKey, RegistrySteamSubKeyName)
    if valType is winreg.REG_SZ:
        return installPath
    else:
        return None
    
def findValheimInstallLocation(steamPath):
    v = vdf.parse(open(steamPath + SteamVDFSubPath))
    for i in v['libraryfolders']:
        if SteamAppIDValheim in v['libraryfolders'][i]['apps']:
            ValheimAbsolutePath = v['libraryfolders'][i]['path'] + SteamValheimInstallSubpath
            os.chdir(ValheimAbsolutePath)
            return 
    
    return

def main():
    exePath = os.path.abspath(__file__)

    # Find Valheim install folder
    if os.name == 'nt':
        # Find Steam install location from Registry
        steamPath = findSteamInstall()
        # Find Valheim install fir from Steam's library config files
        findValheimInstallLocation(steamPath)
        # Program's working folder is now Valheim's root folder

    # Check if Valheim is installed
    if validateModInstall():

        # Download manifest file from http server
        serverIsUp = downloadFile(secreturls.ManifestURL, ManifestFile)

        manifest = configparser.ConfigParser()
        manifest.optionxform = str # Preserve capitalization
        manifest.read(ManifestFile)

        if serverIsUp is not True:
            print("Attention!!! Le serveur distant est innacessible.\r\nLes options seront limitées.")

        # Check Program's version
        versionOk = checkManagerVersion(manifest)
        if versionOk is False:
            print("Téléchargement de la nouvelle version du modpack manager.\r\nL'application va quitter. Veuillez la relancer.")
            # TODO if false download and replace
            downloadFile(manifest['DEFAULT']['url'], exePath)
            return

        # Check if hash list file is present and up-to-date. If not, download a copy and validates it
        hashesFilepath = checkHashesListFileAndDownloadIfRequired(manifest)

        # Parse args when program is invoked
        parser = argparse.ArgumentParser()
        # Used to generate a hash list, when updating modpack. Should not be active for normal use.
        parser.add_argument("-g", "--generate", action='store_true')
        args = parser.parse_args()

        menu = ConsoleMenu("Modpack manager " + Version, "Serveur des Ben shaftés\r\nModpack bien installé.\r\nVoici vos options.")
        if args.generate:
            valheimVRConfig.read(ValheimVRConfigPath)
            augaVRConfig.read(AugaConfigPath)
            menu.append_item(FunctionItem("Générer une liste de md5 des mods (pour développeurs)", generateMD5list, args=[os.path.dirname(exePath)], should_exit=True))
            menu.exit_item.text = "Quitter"
            menu.show()
        else:
            print("Validation de vos fichiers mods. Si vous voyez ce message pendant longtemps, achetez-vous un SSD!")
            if checkMD5(hashesFilepath, not MustMoveExtraFiles, not SilentCheckMD5):
                valheimVRConfig.read(ValheimVRConfigPath)
                augaVRConfig.read(AugaConfigPath)
                if not isVRActive():
                    menu.append_item(FunctionItem("Activer le mode VR", enableVRMode, should_exit=True))
                if not isVRDisabled():
                    menu.append_item(FunctionItem("Désactiver le mode VR", disableVRMode, should_exit=True))

                menu.append_item(FunctionItem("Ré-installer le modpack", installModpack, args=[manifest, hashesFilepath], should_exit=True))
            else:
                menu.append_item(FunctionItem("Installer le modpack", installModpack, args=[manifest, hashesFilepath], should_exit=True))
            menu.exit_item.text = "Quitter"
            menu.show()
    else:
        print("Modpack manager " + Version + "\r\nServeur des Ben shafté\r\n\r\nErreur!!! Le programme ne peut pas trouver votre installation de Valheim.\r\nCe programme devrait se trouver dans le même dossier que l'exécutable valheim.exe.")

if __name__=="__main__":
    main()