import os
import shutil
import argparse
import hashlib
import configparser
from consolemenu import *
from consolemenu.items import *

Version = "0.1"

ValheimExePath = "valheim.exe"

ModFolderPath = "BepInEx"

HashesFilepath = "mod_hashes.properties"

ExtraModFilesFolderPath = "Extra_Mods_Backup"

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
    walk = list(os.walk(path_abs))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            shutil.rmtree(path)
    return

def validateModInstall():
    file_exists = os.path.exists(ValheimExePath)
    valheimVRConfig.read(ValheimVRConfigPath)
    augaVRConfig.read(AugaConfigPath)
    file_exists &= valheimVRConfig.has_option(ValheimVRNonVRCategoryName, ValheimVRNonVREntryName)
    file_exists &= augaVRConfig.has_option(AugaVRCategoryName, AugaVRModeConfigEntryName)
    return file_exists

def isVRActive():
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

def generateMD5list():
    hashesConfig = configparser.ConfigParser()
    hashesConfig.optionxform = str # Preserve capitalization
    hashes = open(HashesFilepath, 'w')
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

def checkMD5():
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

    if extraModFiles:
        print("\r\nErreur! Il y a des fichiers de mods en trop dans votre installation de Valheim.\r\nLa connection au serveur pourrait être refusée!")
        print("Liste des fichiers en trop:")
        print(*extraModFiles, sep = "\r\n")
        for file in extraModFiles:
            fmove(file, os.path.join(ExtraModFilesFolderPath, file))
        print("Les fichiers superflus ont été déplacé dans le dossier " + os.path.join(os.path.abspath(os.getcwd()), ExtraModFilesFolderPath))

    missingMods = []
    wrongHashList = []
    for section in hashesConfig.sections():
        for (filename, hash) in hashesConfig.items(section):
            if not hashesList[os.path.join(section, filename)]:
                missingMods.append(os.path.join(section, filename))
            else:
                if hashesList[os.path.join(section, filename)] not in hashesConfig[section][filename].split(','):
                    wrongHashList.append(os.path.join(section, filename))

    if missingMods:
        print("\r\nErreur! Il manque les mods suivants dans votre installation de Valheim.\r\nLa connection au serveur pourrait être refusée!")
        print(*missingMods, sep = "\r\n")

    if wrongHashList:
        print("\r\nErreur. Les mods suivants sont corrompes dans votre installation de Valheim.\r\nLa connection au serveur pourrait être refusée!")
        print(*wrongHashList, sep = "\r\n")

    return not missingMods and not wrongHashList

def installModpack():
    # TODO Download file from http server
    # TODO unzip in proper location
    return


def main():

    if validateModInstall():
        menu = ConsoleMenu("Modpack manager " + Version, "Serveur des Ben shaftés\r\nModpack bien installé.\r\nVoici vos options.")
        parser = argparse.ArgumentParser()
        parser.add_argument("-g", "--generate", action='store_true')
        args = parser.parse_args()
        if args.generate:
            menu.append_item(FunctionItem("Générer une liste de md5 des mods (pour développeurs)", generateMD5list, should_exit=True))
            menu.exit_item.text = "Quitter"
            menu.show()
        else:
            if checkMD5():
                if not isVRActive():
                    menu.append_item(FunctionItem("Activer le mode VR", enableVRMode, should_exit=True))
                if not isVRDisabled():
                    menu.append_item(FunctionItem("Désactiver le mode VR", disableVRMode, should_exit=True))
            else:
                menu.append_item(FunctionItem("Installer le modpack", installModpack, should_exit=True))
            menu.exit_item.text = "Quitter"
            menu.show()
    else:
        print("Modpack manager " + Version + "\r\nServeur des Ben shafté\r\n\r\nErreur!!! Le modpack n'est pas bien installé.\r\nCe programme devrait se trouve dans le même dossier que l'exécutable valheim.exe.")

if __name__=="__main__":
    main()