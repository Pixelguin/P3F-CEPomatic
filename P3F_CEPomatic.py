import glob, logging, os, pathlib, shutil, subprocess, sys, time
from simple_file_checksum import get_checksum
#os.chdir(os.path.dirname(os.path.abspath(__file__))) # Debug - set working directory to the .py file's location

PROGRAM_NAME = 'CEP-o-matic'
VERSION = '1.0'
LOG_FILENAME = 'P3Flog_' + time.strftime('%Y%m%d-%H%M%S') + '.txt'

# Proper file names
ISO_NAME = 'P3F.iso'
SLUS_NAME = 'SLUS_216.21'
ELF_NAME = 'SLUS_216.21.elf'

# Set directory paths
SETUP_DIR = os.getcwd()
TOOLS_DIR = SETUP_DIR + '\\dependencies'

FILES_DIR = os.path.dirname(SETUP_DIR) + '\\Files'
ISO_DIR = FILES_DIR + '\\iso'
ELF_DIR = FILES_DIR + '\\elf'
BIOS_DIR = FILES_DIR + '\\bios'

# Create logger
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(message)s')

file_handler = logging.FileHandler(LOG_FILENAME, mode = 'w', encoding = 'utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
log.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
log.addHandler(console_handler)

# First log message
log.debug('Created ' + LOG_FILENAME + '\n')

# Set flags
found_iso = False
found_bios = 'none'

def force_rename(old_name, new_name):
    '''
    Tries to rename a file.
    If FileExistsError is caught, the existing file is deleted to ensure renaming can occur.
    '''

    try:
        os.rename(old_name, new_name)
    except FileExistsError:
        os.remove(new_name)
        os.rename(old_name, new_name)

def fatal_error(message):
    log.critical(message + '\n' + LOG_FILENAME + ' may have more information.\n')
    input('Press Enter to end the program...')
    sys.exit()

'''
PROGRAM START
'''
log.info('P3F ' + PROGRAM_NAME + ' ' + VERSION + '\nby Pixelguin\n')

# Check if executable is in the right place
if not SETUP_DIR.endswith('P3F Mods\\Setup'):
    fatal_error('It looks like ' + PROGRAM_NAME + ' isn\'t in the correct directory.\nMake sure this executable is in your P3F Mods\\Setup folder.\n')

for file in os.listdir(SETUP_DIR):
    # iso
    if file.endswith('.iso') and found_iso == False:
        log.info('Found ' + file)

        # Validate P3F disc checksum
        log.info('Validating checksum...')
        checksum = get_checksum(file)
        
        log.debug(file +' has checksum '+ checksum)

        if checksum == '4b16317a11f3089090748b7eca2acbaf':
            log.info('Checksum is valid!\n')

            # Rename iso to the filename P3F CEP expects
            if file != ISO_NAME:
                log.info('Renaming ' + file + ' to ' + ISO_NAME + '...')
                force_rename(file, ISO_NAME)
            
            # Extract SLUS
            log.info('Extracting SLUS_216_21...')
            subprocess.check_call(TOOLS_DIR + '\\7z.exe x -y ' + ISO_NAME + ' ' + SLUS_NAME, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

            # Rename SLUS to the filename P3F CEP expects
            log.info('Renaming ' + SLUS_NAME + ' to ' + ELF_NAME + '...')
            force_rename(SETUP_DIR + '\\' + SLUS_NAME, ELF_NAME)

            # Double-check and set found_iso flag
            if os.path.exists(SETUP_DIR + '\\' + ISO_NAME) and os.path.exists(SETUP_DIR + '\\' + ELF_NAME):
                log.info('ISO and ELF files are OK!\n')
                found_iso = True
            else:
                log.error('Missing either ' + ISO_NAME + ' or '+ ELF_NAME + '!\n')

        else:
            log.error('Checksum is not valid!\n\nYou need an unmodified North American ISO of Persona 3 FES.\nModified disc images, disc images from other regions, and vanilla Persona 3 are NOT compatible.\n')

    # bin
    elif file.endswith('.bin') and found_bios == 'none':
        log.info('Found ' + file)

        # Set found_bios flag
        log.info('Packaged BIOS file found!\n')
        found_bios = file

    # mec
    elif file.endswith('.mec') and found_bios == 'none':
        log.info('Found ' + file)

        # Get filename without extension
        bios_name = pathlib.Path(file).stem

        for otherfile in os.listdir(SETUP_DIR):
            if otherfile.startswith(bios_name) and otherfile != file:
                log.info('Found ' + otherfile)

        # Set found_bios flag
        log.info('Loose BIOS files found!\n')
        found_bios = bios_name

# Check flags and move files
if found_iso == True and found_bios != 'none':
    # Empty BIOS folder
    if os.listdir(BIOS_DIR):
        log.info('Emptying P3F Mods\\Files\\bios folder...')
        files = glob.glob(BIOS_DIR + '\\*')
        for f in files:
            os.remove(f)
            log.debug('Deleted ' + f + ' in bios folder')

    # iso
    log.info('Moving ' + ISO_NAME + ' to P3F Mods\\Files\\iso folder...')
    shutil.move(SETUP_DIR + '\\' + ISO_NAME, ISO_DIR + '\\' + ISO_NAME)

    # elf
    log.info('Moving ' + ELF_NAME + ' to P3F Mods\\Files\\elf folder...')
    shutil.move(SETUP_DIR + '\\' + ELF_NAME, ELF_DIR + '\\' + ELF_NAME)

    # bin
    if found_bios.endswith('.bin'):
        log.info('Moving packaged BIOS to P3F Mods\\Files\\bios folder...')
        shutil.move(SETUP_DIR + '\\' + found_bios, BIOS_DIR + '\\' + found_bios)
    # mec
    else:
        log.info('Moving loose BIOS to P3F Mods\\Files\\bios folder...')
        for movefile in os.listdir(SETUP_DIR):
            if movefile.startswith(found_bios):
                shutil.move(SETUP_DIR + '\\' + movefile, BIOS_DIR + '\\' + movefile)
else:
    if found_iso != True:
        log.error('Missing Persona 3 FES ISO file!')
    if found_bios == 'none':
        log.error('Missing BIOS file(s)!')
    fatal_error('\nCannot continue without all files present!')

# Finished
log.info('\nAll finished!')
input('Press Enter to end the program...')
sys.exit()