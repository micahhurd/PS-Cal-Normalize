# Program Information
program_name = "Scale PSCAL XML Cal Factors"
program_author = "Micah Hurd"
program_version = 1.0
program_date = "2022-09-09"
python_version = 3.8

import standardLibrary as slib
import configuration as cfg
import re
import time


def extract_data_from_pscal_xml(xml_file_path):

    xmlData = slib.readTxtFile(xml_file_path)


    cfFreqList = []
    index_of_freq_list = [] # This indexes the location of frequency within the XML file structure, by line number
    cfList = []
    index_of_cf_list = []  # This indexes the location of cal factor value within the XML file structure, by line number



    slib.printLog("> Reading-in the existing Cal Factor points...")

    # Read in the existing Rho and CF data
    for index, line in enumerate(xmlData):

        try:
            if ("CalFactor diffgr" in line):
                lineList = line.split(" ")
                index_of_freq_list.append(index + 1)
                cFreq = xmlData[index + 1]
                cFreq = re.sub("[^0-9.]", "", cFreq)
                cFreq = float(cFreq)
                cfFreqList.append(cFreq)


                index_of_cf_list.append(index + 2)
                cf = xmlData[index + 2]
                cf = re.sub("[^0-9.]", "", cf)
                # print("cf: {}".format(cf))
                cf = float(cf)
                cfList.append(cf)
        except Exception as err:
            temp_msg = f'Failed to import cal factors out of the XML file!\n\n{err}\n\n'
            slib.printLog(temp_msg)
            slib.error_and_exit(temp_msg)

    slib.printLog(">> Completed!")

    return (cfFreqList, cfList, index_of_freq_list, index_of_cf_list)


def locate_ref_cf_index(freqList, ref_freq):
    locationIndex = -1
    for index, freq in enumerate(freqList):
        if ref_freq == freq:
            locationIndex = index

    if locationIndex > -1:
        return locationIndex
    else:
        temp_str = f"Reference frequency value, {ref_freq} Hz, does not exist in the frequency list!"
        slib.msg_box_simple(temp_str)
        return locationIndex


def scale_cf_list(freqList, original_cf_list, ref_freq, target_scal_factor, resolution=3):
    new_cf_list = []


    index_ref_freq = locate_ref_cf_index(freqList, ref_freq)
    print(index_ref_freq)
    reference_cal_factor = original_cf_list[index_ref_freq]

    delta_factor = target_scal_factor - reference_cal_factor

    for cf in original_cf_list:
        new_cf = cf + delta_factor
        new_cf = round(new_cf, resolution)
        new_cf_list.append(new_cf)

    return new_cf_list


def update_xml_data_by_line(xmlData, update_line_index, update_value):
    def extractValueFromXMLv2(lineData):
        def find_nth(haystack, needle, n):
            start = haystack.find(needle)
            while start >= 0 and n > 1:
                start = haystack.find(needle, start + len(needle))
                n -= 1
            return start

        loc1 = find_nth(lineData, '>', 1)
        loc1 += 1
        val_start = loc1
        loc2 = find_nth(lineData, '<', 2)
        first_half = lineData[:loc1]
        second_half = lineData[loc2:]
        value = lineData.replace(first_half, '')
        value = value.replace(second_half, '')
        outputXMLstring = f'{first_half}val{second_half}'

        return (value, outputXMLstring)

    # print(f'xmlData[0]: {xmlData[0]}')
    uom_list = ['mW', 'mw', 'MW', '%', 'w', 'W']

    line_item = xmlData[update_line_index]
    value, outputXMLstring = extractValueFromXMLv2(line_item)

    # Deal with the occurence of unit of measures being included in the xml data line
    value = value.strip()
    space = True if ' ' in value else False
    line_uom = ' ' if space else ''
    for item in uom_list:
        if item in value:
            line_uom += item
            break

    # Build the new value string
    updated_value = f'{update_value}{line_uom}'
    new_xml_line = outputXMLstring.replace('val', updated_value)
    xmlData[update_line_index] = new_xml_line
    # print(f'xmlData[0]: {xmlData[0]}')

    return xmlData


def update_xml_file(xml_file_path, cf_list, index_of_cf_list):

    try:
        xml_line_data_list = slib.readTxtFile(xml_file_path)

        for index, cf, in enumerate(cf_list):
            xml_line_requiring_update = index_of_cf_list[index]
            xml_line_data_list = update_xml_data_by_line(xml_line_data_list, xml_line_requiring_update, cf)

        # Write the XML data to a file
        with open(xml_file_path, 'w') as filehandle:
            for listItem in xml_line_data_list:
                # print(listItem)
                filehandle.write(listItem)

        return True

    except Exception as err:
        temp_msg = f'Failed to write scaled cal factors to the XML file!\n\n{err}\n\n'
        slib.printLog(temp_msg)

        return False


# def build_values_array(frequencyList, original_cf_list, new_cf_list):
#     array_list = []
#     if len(new_cf_list) == 0:
#         for item in frequencyList:
#             new_cf_list.append("null")
#
#
#     for index, freq in enumerate(frequencyList):
#         line_list = []
#         line_list.append(freq)
#         line_list.append(original_cf_list[index])
#         line_list.append(new_cf_list[index])
#         array_list.append(line_list)
#
#     return array_list


def build_values_array(frequencyList, original_cf_list):
    array_list = []

    for index, freq in enumerate(frequencyList):
        str_freq = slib.convert_to_eng_notation(freq)
        line_list = []
        line_list.append(str_freq)
        line_list.append(original_cf_list[index])
        array_list.append(line_list)

    return array_list


def load_xml_file(xml_file_path, save_bool):
    success_full_load = True
    array_list = []
    freqList = []
    cfList = []


    try:

        new_cf_list = []


        # xml_file_path = "./test.xml"
        xml_file_path = slib.standardize_file_path_format(xml_file_path)

        backup_file_path = cfg.backup_filepath
        backup_file_path = slib.standardize_file_path_format(backup_file_path)

        if save_bool == True:
            slib.copy_file(xml_file_path, backup_file_path)

        freqList, cfList, index_of_freq_list, index_of_cf_list = extract_data_from_pscal_xml(xml_file_path)
        print(freqList)
        print(cfList)

        array_list = build_values_array(freqList, cfList)
    except Exception as err:
        temp_str = f"Failed to load XML File!\n\n{err}"
        success_full_load = False

    return (array_list, freqList, cfList, index_of_cf_list, success_full_load)


class GuiProgramWindow:
    # Requires the PySimpleGUI module to be installed
    import PySimpleGUI as sg
    import threading as thrd
    import time

    def __init__(self, windowTitle, values_array, default_ref_freq, default_file_path='', consoleQuantityOfLines=20):
        self.windowTitle = windowTitle
        self.values_array_for_table = values_array
        self.ref_freq = default_ref_freq
        self.consoleQuantityOfLines = consoleQuantityOfLines
        self.default_file_path = default_file_path


        # Automatically Declared Variables
        self.xmlFileExtension = cfg.pscal_file_extension
        self.xmlFileDescription = cfg.pscal_file_description
        self.TemplateDataFolder = None
        self.CloseBool = False
        self.freq_list = None
        self.cf_list = None
        self.index_of_cf_list = None
        self.ref_freq_index = 0
        self.ref_cf = None
        self.window_value = None
        self.saved_xml_file = ''

        self.sg.theme('SystemDefaultForReal')


    def _thread_function(self):
        # import PySimpleGUI as sg
        # import functools
        inputList = []

        # Set the File Browser File Type
        self.XML_File_Type = [[self.xmlFileDescription, self.xmlFileExtension], ]



        # outputList = []
        # stringOutputList = []
        # stringInputList = []
        # for index, i in enumerate(inputList):
        #     stringInputList.append("{:15}".format(i))

        # Construct the GUI interface
        # self.sg.theme('SystemDefaultForReal')  # Sets the system default theme

        lineLength = 120
        bt = {'size': (7, 2)}
        lb = {'size': (100, 20), 'enable_events': (True), 'font': ('Courier 10')}
        fb = {'size': (115, 20)}
        resource_field = {'size': (80, 20)}
        resource_button = {'size': (23, 1)}

        header = {'font': ('Courier 10')}

        menu_def = [
            ['Misc', 'About...'], ]

        # headers_list = ['Frequency', 'Old Cal Factor', 'New Cal Factor']
        headers_list = ['Frequency (Hz)', 'Calibration Factor (%)']

        ref_cf_settings_field = [
            #[self.sg.Text('')],
            [self.sg.Text('Reference Cal Factor Frequency  (Hz)'),
             self.sg.In(key='-refFreq-', **{'size': (7, 20)}, disabled=True, focus=True)],
            [self.sg.Text('Reference Cal Factor Scale Value (%)'),
             self.sg.In(key='-refScale-', **{'size': (7, 20)}, disabled=True, focus=True)],
            [self.sg.Button('Apply Scaling Value', font=('Helvetica', 10, 'bold'), disabled=True,
                                  key='-scaleBtn-')],
            [self.sg.Text('\n\n\n\n\n\n\n')],
            [self.sg.Text('Program Status:', font=('Helvetica', 10, 'bold'))],
            [self.sg.In('Waiting for user to select an XML file...', key='-statusField-', disabled=True)]
            ]

        layout = [[self.sg.Menu(menu_def, tearoff=False)],
                  # [self.sg.Text('_' * lineLength)],

                  [self.sg.FileBrowse('Browse PSCAL XML File', target='-xmlFile-', file_types=self.XML_File_Type,
                                      initial_folder=self.default_file_path)],
                  [self.sg.In(key='-xmlFile-', enable_events=True, **fb)],
                  # [self.sg.Button('Load DUT Cal Template',  key='-load_template_btn-')],


                  [self.sg.Table(values=self.values_array_for_table, headings=headers_list, max_col_width=35,
                                 auto_size_columns=True,
                                 display_row_numbers=False,
                                 justification='center',
                                 num_rows=10,
                                 key='-table-',
                                 row_height=25,
                                 alternating_row_color='green',
                                 visible=True
                                 ),
                   self.sg.Column(ref_cf_settings_field)
                   ],

                  ]

        # Create the Window
        self.window = self.sg.Window(self.windowTitle, layout, keep_on_top=True)



        while True:
            event, self.window_values = self.window.read()
            if self.CloseBool == False:
                # self.dut_asset_number = values['-dut_asset_in-']
                self.xml_template_filepath = self.window_values['-xmlFile-']


            event_var_type = slib.return_class_type(event)
            # print(f"Class Type: {return_class_type(event)}")
            if not "NoneType" in event_var_type:
                if event in ('-xmlFile-'):
                    self.load_dut_template()

            if event == 'About...':
                self.about_menu_selection()
            if self.CloseBool:
                print("Closed Bool True")
                break
            if event in (self.sg.WIN_CLOSED, 'Continue'):
                break


            if event in ('-scaleBtn-'):

                self.apply_new_scaling()



            if event == 'close':
                break

        self.window.close()


    def load_dut_template(self):
        if not self.saved_xml_file == self.xml_template_filepath:
            save_bool = True
            self.saved_xml_file = self.xml_template_filepath
        else:
            save_bool = False


        print('Load DUT template')

        if len(self.xml_template_filepath) == 0:
            slib.msg_box_simple("You must browse and select the PSCAL XML File First!")
        elif not slib.file_check_exists(self.xml_template_filepath):
            slib.msg_box_simple(f"The template file does not exist!\n\nTried: {self.xml_template_filepath}")
            self.window['-xmlFile-'].update('')
        else:

            # successful_template_load = get_dut_template_data(self.xml_template_filepath)
            slib.printLog(f"Loading XML file: {self.xml_template_filepath}", console=False)
            self.values_array_for_table, self.freq_list, self.cf_list, self.index_of_cf_list, successful_template_load = load_xml_file(self.xml_template_filepath, save_bool)
            slib.printLog(f"Found Freq List: {self.freq_list}", console=False)
            slib.printLog(f"Found Cal Factor List: {self.index_of_cf_list}", console=False)
            slib.printLog(f"Template loaded successfully? {successful_template_load}", console=False)

            if not successful_template_load:
                slib.msg_box_simple(f"Could not load XML File at {self.xml_template_filepath}\n\nSee Log for Details")
                self.xml_template_filepath = ''
                self.window['-xmlFile-'].update('')
                return False

            temp_int = locate_ref_cf_index(self.freq_list, self.ref_freq)
            self.ref_cf_index = temp_int if temp_int > -1 else 0
            self.ref_cf = self.cf_list[self.ref_cf_index]
            # Update the window with the ref freq value


            # Update fields
            self.window['-table-'].update(self.values_array_for_table)
            self.window['-refFreq-'].update(f'{slib.convert_to_eng_notation(self.ref_freq)}')

            self.window['-refScale-'].update(self.ref_cf)

            self.lock_unlock_lower_fields(locked=False)

            slib.printLog(f'Current XML file: {self.xml_template_filepath}', console=False)
            self.prgrm_status("Loaded XML File!")


    def lock_unlock_lower_fields(self, locked=False):
        # self.window.FindElement('Browse Standard Sensor Data File').Update(disabled=locked)


        self.window['-refFreq-'].Update(disabled=locked)
        self.window['-refScale-'].Update(disabled=locked)
        self.window['-scaleBtn-'].Update(disabled=locked)
        self.window['-table-'].Update(visible=True)



    def apply_new_scaling(self):

        success_flag = False

        # print(event, values)
        self.ref_freq = float(self.window_values['-refFreq-'])

        slib.printLog(f"reference Frequency from GUI: {self.ref_freq}", console=False)
        target_scal_factor = float(self.window_values['-refScale-'])
        slib.printLog(f"target scale factor from GUI: {target_scal_factor}", console=False)

        new_cf_list = scale_cf_list(self.freq_list, self.cf_list, self.ref_freq, target_scal_factor)
        slib.printLog(f"New scaled cal factor list: {new_cf_list}", console=True)
        success_flag = update_xml_file(self.xml_template_filepath, new_cf_list, self.index_of_cf_list)
        slib.printLog(f"Successfully updated XML File?: {success_flag}", console=False)

        if success_flag == False:
            slib.msg_box_simple("Failed to write the new scaled cal factors!")
        else:
            slib.printLog("Successfully wrote new CF values to XML file", console=False)
            self.load_dut_template()
            self.prgrm_status("Saved new cal factors!")


    def prgrm_status(self, message):

        self.window['-statusField-'].update(message)


    def about_menu_selection(self):
        temp_str = f'You must be pretty bored to press the \"About\" button. Sorry things aren\'t more exciting right now.' \
                   f'\n\n' \
                   f'So I said in my heart, \"As death happens to the fool, death also happens to me, so why was ' \
                   f'I then more wise than a fool?\" Then I said in my heart, \"This also is vanity.\" For there is ' \
                   f'no more remembrance of the wise than of the fool forever, since all that now is will be forgotten' \
                   f' in the days to come. And how does a wise man die? The same way as the fool! Therefore I hated ' \
                   f'life because the work that was done under the sun was distressing to me, for all is vanity and ' \
                   f'grasping for the wind. Then I hated all my labor in which I had toiled under the sun, because I ' \
                   f'must leave it to the man who will come after me. And who knows whether he will be wise or a fool? ' \
                   f'Yet he will rule over all my labor in which I toiled and in which I have shown myself wise under ' \
                   f'the sun. This also is vanity. Therefore I turned my heart and despaired of all the labor in which' \
                   f' I had toiled under the sun. For there is a man whose labor is with wisdom, knowledge, and skill;' \
                   f' yet he must leave his heritage to a man who has not labored for it. This also is vanity and' \
                   f' a great evil. For what has man for all his labor, and for the striving of his heart with which' \
                   f' he has toiled under the sun? For all his days are sorrowful, and his work burdensome; even in' \
                   f' the night his heart takes no rest. This also is vanity... For what happens to the sons of men ' \
                   f'also happens to animals; one thing befalls them: as one dies, so dies the other. Surely, they all' \
                   f' have one breath; man has no advantage over animals, for all is vanity. All go to one place: all' \
                   f' are from the dust, and all return to dust. Who knows the spirit of the sons of men, which goes' \
                   f' upward, and the spirit of the animal, which goes down to the earth? So I perceived that nothing' \
                   f' is better than that a man should rejoice in his own works, for that is his heritage. For who can ' \
                   f'bring him to see what will happen after him?... For who knows what is good for man in life, all' \
                   f' the days of his vain life in which he passes like a shadow? Who can tell a man what will happen' \
                   f' after him under the sun?... Let us hear the conclusion of the whole matter: Fear God and keep His' \
                   f' commandments, for this is man’s all. For God will bring every work into judgment, including every' \
                   f' secret thing, whether good or evil.\n\n- Selections from Ecclesiastes'

        slib.yes_no_other_popup(temp_str, other_str_text='  N/A ', btn_focus=1, window_title='The About Window...',
                           lineLength=120)
        temp_str = f'About\n\n' \
                   f'Program Name: {program_name}\n' \
                   f'Author: {program_author}\n' \
                   f'Version: {program_version}\n' \
                   f'Release Data: {program_date}\n' \
                   f'Python Version: {python_version}'
        slib.msg_box_simple(temp_str)


    def open_window(self):
        # self.thread1 = self.thrd.Thread(target=self._thread_function)
        # self.thread1.start()
        self._thread_function()


    def close_window(self):
        print("attempting to close thread")
        time.sleep(1)
        self.CloseBool = True
        self.window.close()
        # self.thread1.join(timeout=1)
        print("Thread was closed.")


if __name__ == '__main__':
    load_path = slib.standardize_file_path_format(cfg.default_load_path)
    gui = GuiProgramWindow(windowTitle=program_name, values_array=[], default_ref_freq=cfg.default_ref_freq, default_file_path=load_path)
    # gui.TemplateDataFolder = cwd + "templates"
    gui.open_window()







