from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo
from aqt import dialogs
import random
from aqt.qt import QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget, Qt

from anki import cards
from aqt.reviewer import Reviewer
from anki.hooks import wrap

import csv
from datetime import datetime
from typing import *
import time

import json


_C = 'deck:"{}"'
_A = 'name'

newVocabularyNoteKey = "Keyword"
DefaultDeckName = "My Quizz Deck"
NoteFileKeyAnswer = "Keyword"


def get_deck_name(deck_id):
    try:
        deck_name = mw.col.decks.get(deck_id)[_A]
        return deck_name
    except KeyError:
        return

class PracticeTestDialog(QDialog):
    def __init__(self, parent, deckId):
        super().__init__(parent)
        self.deckId = deckId

        mainLayout = QVBoxLayout()

        # Name field
        name_label = QLabel("Name:")
        self.deckNameInput = QLineEdit(DefaultDeckName)
        self.deckNameInput.setReadOnly(True)  # Set the input to read-only
        mainLayout.addWidget(name_label)
        mainLayout.addWidget(self.deckNameInput)

        # Number of cards field
        number_cards_label = QLabel("Number of cards:")
        self.number_card_random = QLineEdit("3")
        mainLayout.addWidget(number_cards_label)
        mainLayout.addWidget(self.number_card_random)

        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.build_button = QPushButton("Build")
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.build_button)


        mainLayout.addLayout(button_layout)
        self.cancel_button.clicked.connect(self.reject)
        self.build_button.clicked.connect(self.create_new_deck)

        self.setWindowTitle('Create Quizz - ' + get_deck_name(self.deckId))
        self.setLayout(mainLayout)
        # Set the dialog size
        self.resize(500, 200)  # Width: 400, Height: 300

    # Button actions
    def create_new_deck(self):
        print("create_new_deck")
        targetDeckName = get_deck_name(self.deckId)
        newDeckName = self.deckNameInput.text()
        print("newDeckName: ", newDeckName)

        # Check if the deck already exists
        new_deck_id = mw.col.decks.id(newDeckName, create=False)
        if new_deck_id:
            # Delete the existing deck
            mw.col.decks.rem(new_deck_id)

        new_deck_id = mw.col.decks.id(newDeckName, create=True)


        # Create a new deck
        # new_deck_id = mw.col.decks.id(newDeckName, create=True)
        # if not new_deck_id:
        #     showInfo(f"Failed to create the deck '{newDeckName}'.")
        #     return

        # deck_name = mw.col.decks.get(target_deck_id)[_A]
        search_string = _C.format(targetDeckName)
        print("search_string: ", search_string)
        print("self.number_card_random.text()", self.number_card_random.text())
        note_ids = mw.col.find_notes(search_string)
        random.shuffle(note_ids)
        note_ids = note_ids[:int(self.number_card_random.text())]
        print("lenth of random: ", len(note_ids))

        # Retrieve the deck configuration
        deck_config = mw.col.decks.get_config(new_deck_id)

        # Modify the desired options
        deck_config['new']['perDay'] = int(self.number_card_random.text())  # Example: Set the number of new cards per day to 20
        deck_config['rev']['perDay'] = int(self.number_card_random.text()) * 2  # Example: Set the number of review cards per day to 100

        # Update the deck with the new configuration
        mw.col.decks.update_config(deck_config)

        # Clone selected cards into the new deck
        cloned_count = 0
        for nid in note_ids:
            original_note = mw.col.get_note(nid)
            # for key, value in note.items():
            #     if key == newVocabularyNoteKey:
            #         print("keyword: ", value)

            # Create a new note with the same fields and model as the original
            new_note = mw.col.new_note(original_note.note_type())
            for field_name in original_note.keys():
                # print("field_name: ", field_name)
                new_note[field_name] = original_note[field_name]

            # Assign the new note to the new deck
            new_note.note_type()["did"] = new_deck_id
            # Add the cloned note to the collection
            if mw.col.add_note(new_note, new_deck_id):
                cloned_count += 1

        # Save changes and refresh
        mw.col.save()
        mw.reset()

        create_file_with_deck_name(new_deck_id, targetDeckName)

        showInfo(f"New deck '{newDeckName}' created with {cloned_count} cloned cards!")
        self.accept()  # Close the dialog

    def show(self):
        super().show()


def add_practice_tests_option(menu, deckId):
    action = menu.addAction('create quizz for 4000 essential english words 222')
    action.triggered.connect(PracticeTestDialog(mw, deckId).show)

gui_hooks.deck_browser_will_show_options_menu.append(add_practice_tests_option)



# from anki.hooks import card_did_render
#
# def modify_card_text(templateRenderOutput, templateRenderContext):
#     # print("templateRenderOutput: ", templateRenderOutput)
#     # print("TemplateRenderContext: ", templateRenderContext)
#     # # Add a footer to the card's text
#     # print("templateRenderOutput.question_text 1:  ", templateRenderOutput.question_text)
#     templateRenderOutput.question_text = templateRenderOutput.question_text + "<div style='color: gray;font-size: 40px;'>Footer: Study Hard! xxxxx </div>"
#     # print("templateRenderOutput.question_text 2: ", templateRenderOutput.question_text)
#     return templateRenderOutput
#
# # Append the function to the hook
# card_did_render.append(modify_card_text)


# Define the custom action function
def custom_review_button_action(reviewer:Reviewer, card: cards.Card, ease):
    deck_name = mw.col.decks.current()["name"]
    deckId = mw.col.decks.current()["id"]
    print("[custom_review_button_action] deck name: ", deck_name)

    # Check if we are in the specific deck
    if deck_name != DefaultDeckName:
        # default action
        reviewer._answerCard(ease)
        return

    # specific deck
    print("[custom_review_button_action] User press button: ", ease)

    # print("=========== card info ===========")
    # print_card_info(card)
    # print("=========== reviewer info ===========")
    # show_reviewer_info(reviewer)

    startTime = card.timer_started
    isCorrect = compare_answers(reviewer.typeCorrect, reviewer.typedAnswer)
    save_review_data(deckId, reviewer.typeCorrect, reviewer.typedAnswer, startTime, isCorrect)
    # Call the default action
    print("override ease: ", ease)
    reviewer._answerCard(ease)

# Append the function to the hook
gui_hooks.reviewer_did_answer_card.append(custom_review_button_action)



def custom_reviewer_will_answer_card(
 ease_tuple: tuple[bool, Literal[1, 2, 3, 4]], reviewer, card: cards.Card
) -> tuple[bool, Literal[1, 2, 3, 4]]:
    # Modify the ease rating if certain conditions are met
    print("[custom_reviewer_will_answer_card] ease_tuple: ", ease_tuple)
    should_continue, ease = ease_tuple
    if isSpecialDeck():
        ease = 4  # Always rate as 'Easy' for the special deck
    return should_continue, ease

# Append the custom function to the hook
gui_hooks.reviewer_will_answer_card.append(custom_reviewer_will_answer_card)

def show_reviewer_info(reviewer: Reviewer):
    """
    Print all information of the Reviewer instance.

    Args:
        reviewer (Reviewer): The Reviewer instance.
    """
    attributes = dir(reviewer)
    for attribute in attributes:
        if not attribute.startswith("__"):
            value = getattr(reviewer, attribute)
            print(f"{attribute}: {value}")

def print_card_info(card: cards.Card):
    """
    Print all information of the Card instance.

    Args:
        card (cards.Card): The Card instance.
    """
    attributes = dir(card)
    for attribute in attributes:
        if not attribute.startswith("__"):
            value = getattr(card, attribute)
            print(f"{attribute}: {value}")


def customNumberOfButtons(buttons_tuple, reviewer, card):
    if not isSpecialDeck():
        return buttons_tuple
    button_count = mw.col.sched.answerButtons(card)
    print("[customNumberOfButtons] button_count: ", button_count)

    customButton = []
    customButton.append((4, "Submit"))
    return tuple(customButton)

gui_hooks.reviewer_will_init_answer_buttons.append(customNumberOfButtons)



def isSpecialDeck():
    deck_name = mw.col.decks.current()["name"]
    print("deck_name: ", deck_name)
    return deck_name == DefaultDeckName


def get_note_info_from_card_id(card_id):
    card = mw.col.get_card(card_id)
    note = card.note()

    note_info = {
        "Note ID": note.id,
        "Note Type": note.note_type()["name"],
        "Tags": note.tags,
        "Fields": {field: note[field] for field in note.keys()}
    }

    for key, value in note_info.items():
        print(f"{key}: {value}")
    return

def compare_answers(correct: str, answer: str) -> bool:
    """
    Compare two strings after converting them to lower case, trimming spaces, and splitting by commas.

    Args:
        correct (str): The correct string to compare.
        answer (str): The answer string to compare.

    Returns:
        bool: True if the strings are equal, False otherwise.
    """
    correct_parts = [part.strip().lower() for part in correct.split(",")]
    answer_parts = [part.strip().lower() for part in answer.split(",")]
    return correct_parts == answer_parts



def create_file_with_deck_name(deck_id: any, cloned_deck_name: str):
    """
    Create a file with the deck's ID and deck name as the file name.

    Args:
        deck_id (str): The ID of the deck.
        cloned_deck_name (str): The name of the cloned deck.
    """
    dirname = os.path.dirname(__file__)
    # Ensure the filename is safe for the filesystem
    fileName = f"{deck_id}_{cloned_deck_name}.txt"
    fileName = fileName.strip().replace(" ", "_")
    filePath = os.path.join(dirname, fileName)

    print("[create_file_with_deck_name] filePath: ", filePath)

    # Create an empty file
    with open(filePath, 'w') as file:
        pass  # Just create the file without writing any data

def save_review_data(deck_id:any, type_correct:str, typed_answer:str, time_start: int, isCorrect: bool):
    """
    Save review data to a CSV file named after the deck ID.

    Args:
        deck_id (str): The ID of the deck.
        type_correct (str): The correct type.
        typed_answer (str): The typed answer.
        time_start (datetime): The start time of the review.
    """
    # Get the directory name of the current file
    dirname = os.path.dirname(__file__)
    filePath = os.path.join(dirname, f"{deck_id}.csv")
    fieldnames = ['typeCorrect', 'typedAnswer', 'timeStart', 'timeEnd', 'timeTakenInSec', 'isCorrect']
    # Get the current time in seconds since the epoch
    current_time = time.time()

    # Convert the time to a datetime object
    startDateTime = datetime.fromtimestamp(time_start)
    currentDateTime = datetime.fromtimestamp(current_time)


    # Format the datetime object as a string
    timeTakenInSec = current_time - time_start

    try:
        with open(filePath, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write the header only if the file is empty
            if file.tell() == 0:
                writer.writeheader()

            writer.writerow({
                'typeCorrect': type_correct,
                'typedAnswer': typed_answer,
                'timeStart': startDateTime.strftime('%Y-%m-%d %H:%M:%S'),
                'timeEnd': currentDateTime.strftime('%Y-%m-%d %H:%M:%S'),
                'timeTakenInSec': timeTakenInSec,
                'isCorrect': isCorrect
            })
        print(f"[save_review_data] Data saved successfully. {filePath}")
    except Exception as e:
        print(f"[save_review_data] Failed to save data {filePath}; err: {e}")