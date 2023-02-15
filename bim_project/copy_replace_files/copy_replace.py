import pandas as pd
import os
import shutil

''' Some bullshit script to copy/replace files from the given excel files. '''

def read_excel_file():
    excel_file = input("Enter excel file name: ")
    try:
        data = pd.read_excel(excel_file)
    except FileNotFoundError:
        print('File not found')
        return False
    return data


def copy_files():

    data = read_excel_file()
    if not data:
        return
    filenames_column:str          = data[data.columns.ravel()[0]] # First column. data['Name']
    start_fileLocation_column:str = data[data.columns.ravel()[1]] # Second column. data['Folder Path']
    end_fileLocation_column:str   = data[data.columns.ravel()[2]] # Third column. data['Итоговая папка']

    # Creating a file to check the progress/result
    result_filename:str = 'copy_results.log'
    if os.path.isfile(result_filename):
        os.remove(result_filename)
    files_copied:int = 0
    ext:str = '.pdf'
    with open(result_filename, 'a', encoding='utf-8') as file:
        for line in range(len(start_fileLocation_column)):

            # Check if this is an empty line in the list
            if pd.isna(start_fileLocation_column[line]):
                continue

            # Check out the slash at the end of the string in both locations
            start_fileLocation:str = \
                start_fileLocation_column[line] if start_fileLocation_column[line][-1] == '\\' else start_fileLocation_column[line] + '\\'
            end_fileLocation:str   = \
                end_fileLocation_column[line] if end_fileLocation_column[line][-1] == '\\' else end_fileLocation_column[line] + '\\'
            
            # Check out the extension of the file
            filename:str = \
                filenames_column[line] if os.path.splitext(filenames_column[line][1]) == ext else filenames_column[line] + ext

            check_file_at_start:bool  = os.path.isfile(start_fileLocation + filename)
            check_file_at_finish:bool = os.path.isfile(end_fileLocation + filename)

            if check_file_at_start and not check_file_at_finish:
                try:
                    shutil.copyfile(start_fileLocation + filename, end_fileLocation + filename)
                    message = "Copying file: " + filename
                    print(message)
                except (OSError, shutil.Error) as error:
                    print("Error:\n",error,'\n')
                    continue
                file.write(message)
                files_copied += 1
            elif not check_file_at_start:
                message = "No such file: " + filename
                file.write(message + '\n')
                print(message)
            elif check_file_at_finish:
                message = "File already exists: " + filename
                file.write(message + '\n')
                print(message)
            else:
                print("Unpredictable behaviour.")
                return False

        print("\nTotal files copied: " + str(files_copied))
        file.write("\nTotal files copied: " + str(files_copied))
    
    return True


def rename_files():

    data = read_excel_file()
    if not data:
        return
    old_filenames_column:str  = data[data.columns.ravel()[0]] # First column data
    new_filenames_column:str  = data[data.columns.ravel()[1]] # Second column data
    fileLocation_column:str   = data[data.columns.ravel()[2]] # Third column data
    
    # Creating a file to check the progress/result
    result_filename:str = 'rename_results.log'
    if os.path.isfile(result_filename):
        os.remove(result_filename)

    files_renamed:int = 0
    ext:str = '.pdf'
    with open(result_filename, 'a', encoding='utf-8') as file:
        for line in range(len(new_filenames_column)):

            # Check if this is an empty line in the list.
            if pd.isna(new_filenames_column[line]) or pd.isna(old_filenames_column[line]) or pd.isna(fileLocation_column[line]):
                continue

            # Check out the slash at the end of the string in both locations
            fileLocation:str = fileLocation_column[line] if fileLocation_column[line][-1] == '\\' else fileLocation_column[line] + '\\'

            # Check out the extension of the file
            old_filename:str = old_filenames_column[line]
            new_filename:str = new_filenames_column[line]

            old_filename = old_filename if os.path.splitext(old_filename)[1] == ext else old_filename + ext
            new_filename = new_filename if os.path.splitext(new_filename)[1] == ext else new_filename + ext

            # Check if the file exists
            check_file_exists:bool  = os.path.isfile(fileLocation + old_filename)
            if check_file_exists:
                try:
                    os.rename(fileLocation + old_filename, fileLocation + new_filename)
                    message = "file:" \
                               + "\n  previous name: " + old_filename \
                               + "\n  new name: " + new_filename
                    print(message)
                except OSError as error:
                    print("Error:\n",error,'\n')
                    continue
                file.write(message)
                files_renamed += 1
            elif not check_file_exists:        
                message = "No such file: " + old_filename
                file.write(message + '\n')
                print(message)
            else:
                print("Unpredictable behaviour.")
                return False

        print("\nTotal files renamed: " + str(files_renamed))
        file.write("\nTotal files renamed: " + str(files_renamed))
    
    return True


def main():
    specify_an_action:str = input('Choose an action for files. Copy(1) or Replace(2): ')    
    if specify_an_action == '1':
        copy_files()
    elif specify_an_action == '2':
        rename_files()
    else:
        print('Incorrect choice.')
        return False

if __name__ == '__main__':
    main()



