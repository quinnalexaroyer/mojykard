# mojykard (Version 0.1)
Flashcard program written in Python tkinter. It requires Python 3.7.

The name comes from the constructed language Lojban, which translates "memory card". This program is a work in progress.

The first steps to use the program are to create a database file and user account. After starting the program, enter a name 
and push "New File". The extension ".db" will be added automatically, so don't type an extension. Then select the file in the 
drop down list and push "Select File". Next, enter a username and push "Add User". Select your username from the dropdown list 
and push "Select User".

= Create a deck =

After selecting your user account, you can create a deck from the "Edit" menu at the top and selecting "New Deck". As this program 
is a work in progress, it may create problems if you try to create or edit a deck before you select your user account, so make sure
you have selected your account first. After clicking "New Deck", enter a name for the deck and the number of sides (which must be 
at least 2). Push "Create Deck". The program does not currently alert the user that the creation was successful so it might seem 
like nothing happened. Next you will need to close the program and open it again to start editing the deck. Remember to select your
user account after opening the program again.

= Editing the deck =

Under the "Edit" menu, select either "Edit Cards (Singular Mode)" or "Edit Cards (Multiple Mode)". To begin editing the deck, 
select the deck's name from the list and push the "Select" button. The decks name should appear under "Deck Selected:" at the 
right. Alternatively, you can type the name of the deck in the field and the left and push "Enter", but you still have to push 
"Select" after "Enter". You can now begin editing the cards. Push "Save and Close" when finished.

= Using the deck =

To start studying a deck, your account must be "using" it first. Under the "User" menu click "Use Deck". When you click on the name 
of the deck, checkboxes will appear below numbered from 1 to the number of sides in the deck. This is to indicate which sides the 
program will show you when studying. For example, if the deck has two sides, and you want it to always show you side 1 while you 
try to guess side 2, you would check box #1 and leave #2 unchecked. If you sometimes want it to show you side 1 while you guess 
side 2, and sometimes show you side 2 while you guess side 1, check both boxes. Once you have checked the boxes as you wish, push 
the "Select" button and your account will now be "using" the deck. It should display a message below the checkboxes and above the 
"Finished" button saying that the deck is now being used. Push the "Finish" button to return to the previous screen. You may have
to close and open the program again to begin studying.

= Studying =

After you log into your account, there will be a screen with a button labeled "Begin Session" and a list of each deck your 
account is using. To begin studying, click the checkbox to the left of the name of the deck then push "Begin Session". This will 
take you to another screen. Push "Begin" on this screen and the session will begin. When reviewing each card, push a button 
numbered from 0 to 5 based on how well you know the answer to this card (with 5 meaning you know it well, and 0 not at all).
After you push a rating, it will show you the other side(s). Push "New Card" to review another card and "End Session" when you
are finished.

= To Do List =

This README file is not complete and I need to finish it later.

The following features should be added to later versions:
- Changes made should be reflected immediately so the user does not have to close and open the program.
- Some menu items should be inactivated until after the user has logged into their account.
- Sessions are logged in a file called mojykard_log.txt. I need to add a way for the user to turn off this feature if desired.
