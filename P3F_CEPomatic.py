import logging, os, shutil, subprocess, sys, time
from pathlib import Path
from simple_file_checksum import get_checksum
#os.chdir(os.path.dirname(os.path.abspath(__file__))) # Debug - set working directory to the .py file's location

PROGRAM_NAME = 'CEP-o-matic'
VERSION = '1.3'

# Proper file and directory names
SETUPDIR_NAME = Path('P3F Mods/Setup/')
ISO_NAME = 'P3F.iso'
SLUS_NAME = 'SLUS_216.21'
ELF_NAME = 'SLUS_216.21.elf'

# Set directory paths
SETUP_DIR = Path(os.getcwd())
TOOLS_DIR = SETUP_DIR / 'dependencies'

LOGS_DIR = SETUP_DIR.parents[0] / 'Logs/'
LOGS_FILE = LOGS_DIR / f"CEPomaticLog_{time.strftime('%Y%m%d-%H%M%S')}.txt"

FILES_DIR = SETUP_DIR.parents[0] / 'Files/'
ISO_DIR = FILES_DIR / 'iso/'
ELF_DIR = FILES_DIR / 'elf/'
BIOS_DIR = FILES_DIR / 'bios/'
MEMCARDS_DIR = FILES_DIR / 'memcards/'

# Create logger
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)

file_formatter = logging.Formatter('>%(levelname)-10s %(message)s') # Show level in log file but not console
console_formatter = logging.Formatter('%(message)s')

file_handler = logging.FileHandler(LOGS_FILE, mode = 'w', encoding = 'utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)
log.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
log.addHandler(console_handler)

# First log message
log.debug(f'Created {LOGS_FILE}\n')

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
    log.critical(f'{message}\nA log is available at {LOGS_FILE}.\n')
    input('Press Enter to end the program...')
    sys.exit()

'''
PROGRAM START
'''
log.info(f'P3F {PROGRAM_NAME} {VERSION}\nby Pixelguin\n')

# Check if executable is in the right place
log.debug(f'{PROGRAM_NAME} is in {SETUP_DIR}')
if not SETUP_DIR.parents[1] / SETUPDIR_NAME == SETUP_DIR:
    fatal_error(f'It looks like {PROGRAM_NAME} isn\'t in the correct directory.\nMake sure this executable is in your {SETUPDIR_NAME} folder.\n')

# Scan for files
for file in os.listdir(SETUP_DIR):
    # iso
    if file.endswith('.iso') and found_iso == False:
        log.info(f'Found {file}')

        # Validate P3F disc checksum
        log.info('Validating checksum...')
        checksum = get_checksum(file)
        
        log.debug(f'{file} has checksum {checksum}')

        if checksum == '4b16317a11f3089090748b7eca2acbaf':
            log.info('Checksum is valid!\n')

            # Rename iso to the filename P3F CEP expects
            if file != ISO_NAME:
                log.info(f'Renaming {file} to {ISO_NAME}...')
                force_rename(file, ISO_NAME)
            
            # Extract SLUS
            log.info(f'Extracting {SLUS_NAME}...')
            subprocess.check_call([TOOLS_DIR / f'7z.exe', 'x', '-y', ISO_NAME, SLUS_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

            # Rename SLUS to the filename P3F CEP expects
            log.info(f'Renaming {SLUS_NAME} to {ELF_NAME}...')
            force_rename(SETUP_DIR / SLUS_NAME, ELF_NAME)

            # Double-check and set found_iso flag
            if os.path.exists(SETUP_DIR / ISO_NAME) and os.path.exists(SETUP_DIR / ELF_NAME):
                log.info('ISO and ELF files are OK!\n')
                found_iso = True
            else:
                log.error(f'Missing either {ISO_NAME} or {ELF_NAME}!\n')

        else:
            log.error('Checksum is not valid!\n\nYou need an unmodified North American ISO of Persona 3 FES.\nModified disc images, disc images from other regions, and vanilla Persona 3 are NOT compatible.\n')

    # bin
    elif file.endswith('.bin') and found_bios == 'none':
        log.info(f'Found {file}')

        # Set found_bios flag
        log.info('Packaged BIOS file found!\n')
        found_bios = file

    # mec
    elif file.endswith('.mec') and found_bios == 'none':
        log.info(f'Found {file}')

        # Get filename without extension
        bios_name = Path(file).stem

        # Find other BIOS files with the same filename
        for otherfile in os.listdir(SETUP_DIR):
            if otherfile.startswith(bios_name) and otherfile != file:
                log.info(f'Found {otherfile}')

        # Set found_bios flag
        log.info('Loose BIOS files found!\n')
        found_bios = bios_name

    # ps2
    elif file.endswith('.ps2'):
        log.info(f'Found {file}')

        # Move into memcards folder
        log.info(f'Moving memcard {file} to {MEMCARDS_DIR}...\n')
        shutil.move(SETUP_DIR / file, MEMCARDS_DIR / file) # Using move with the exact file path overwrites existing file

# Check flags and move files
if found_iso == True and found_bios != 'none':
    # Empty BIOS folder
    if os.listdir(BIOS_DIR):
        log.info(f'Emptying {BIOS_DIR}...')
        for f in BIOS_DIR.glob('*.*'):
            os.remove(f)
            log.debug(f'Deleted {f}')

    # iso
    log.info(f'Moving {ISO_NAME} to {ISO_DIR}...')
    shutil.move(SETUP_DIR / ISO_NAME, ISO_DIR / ISO_NAME) # Using move with the exact file path overwrites existing file

    # elf
    log.info(f'Moving {ELF_NAME} to {ELF_DIR}...')
    shutil.move(SETUP_DIR / ELF_NAME, ELF_DIR / ELF_NAME)

    # bin
    if found_bios.endswith('.bin'):
        log.info(f'Moving packaged {found_bios} to {BIOS_DIR}...')
        shutil.move(SETUP_DIR / found_bios, BIOS_DIR / found_bios)
    # mec
    else:
        log.info(f'Moving loose BIOS {found_bios} to {BIOS_DIR}...')
        for movefile in os.listdir(SETUP_DIR):
            if movefile.startswith(found_bios):
                shutil.move(SETUP_DIR / movefile, BIOS_DIR / movefile)
                log.debug(f'Moved {movefile}')
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