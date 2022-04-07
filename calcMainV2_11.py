from CombinedCaculatorV_FINAL2 import *
import sys
import math


# This class is used to override the power method of the built-in int class.
class Int(int):
    def __pow__(self, other, **kwargs):
        return math.pow(self, other)

# This class is used to override the power method of the built-in float class.
class Float(float):
    def __pow__(self, other, **kwargs):
        return math.pow(self, other)


class Calculator(Ui_MainWindow):
    """
    This is where all the logic of the calculator reside.
    Uses the .py file generated from the .ui file we made in QTDesigner.
    """
    def __init__(self, window):
        self.setupUi(window)

        self.window = window

        # Here is our list of buttons and operations that we will use in the program.
        self.numberList = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
        self.simpleOperationsList = ("/", "x", "+", "X^y")
        self.scientificOperationsList = ("Sin", "Cos", "Tan", "Sin^(-1)", "Cos^(-1)", "Tan^(-1)", "Sqrt", "Log")

        # Basically records the history of the calculator; used in the operation of the backspace button.
        self.previousStates = []  # empty because we fill them up as we progress with the program

        # Keeps track of all open brackets while the user inputs data into the calculator;
        # will be empty once all brackets are closed.
        self.bracketsList = []

        self.numbersInExp = []  # this will keep track of the start and end positions of numbers entered
        self.numberStartEnd = []  # the start and end numbers positions are stored here and then added to numbersInExp
        self.lastClosedBracketSet = None  # it will wrap the number with any scientific operation
        self.lastSimpleOperationPos = -1  # this will help position the scientific operation incase there is no brackets

        self.lastAllowedInput = ""  # keeps track of the last number,for eg: we can decide what would go next after
        # typing an operator like we can't put ")" after +
        self.pointInCurrentNumber = False  # detects the decimal point, it will turn true when we put a point.
        self.percentInNumber = False

        self.answerDecimalLimit = 10  # Max number of decimal places the final answer will have.
        self.digitCount = 0  # it's a counter to keep track of how many digits or operators you have used
        self.digitLimit = 15  # max number of digits than can be entered is 15
        self.operationsCount = 0
        self.operationsLimit = 40  # number of times you can use operators at once is 40 times

        self.mainDisplayString = ""  # this is the bigger part of the text box to display how inputs and its stored here
        self.secondDisplayString = ""  # same for the smaller part
        self.secondDisplay = self.secondDisplayPage1  # both text-labels are equal in simple calculator
        self.mainDisplay = self.mainDisplayPage1  # this variable is equal to simple calculator mainDisplay

        # Used to co-ordinate the behaviour of the self.add() method, based on the button that the user pressed.
        self.addTable = {
            (self.simpleOperationsList + ("%",)): lambda x: self.add_simple_operation(x),
            ("(", ")"): lambda x: self.add_bracket(x),
            self.scientificOperationsList: lambda x: self.add_scientific_operation(x),
            self.numberList: lambda x: self.add_number(x),
            (".",): lambda x: self.add_point(x),
            ("-",): lambda x: self.add_minus(x)

        }

        # Used to co-ordinate the behaviour of the self.button_handler() method,
        # based on the button that the user pressed, and the last inputted character;
        # used for input validation.
        self.validationTable = {
            # here are the possibilities of using these operation lists, this will make sure that we don't type random
            # operations and make it work, it should be an error
            (self.simpleOperationsList + ("%",)): {
                (self.simpleOperationsList + ("-",)): self.switch_out,
                (self.numberList + self.scientificOperationsList + (")", "%")): self.add,
                ("(", ".", "", "(-", "Error", "End"): self.ignore
            },

            ("AC",): {
                (self.simpleOperationsList + self.scientificOperationsList + self.numberList + (
                    "(", ")", ".", "-", "", "Error", "(-", "End", "%")): self.clear
            },

            ("(",): {
                (self.simpleOperationsList + ("(", "-", "", "Error", "(-", "End", "%")): self.add,
                (self.numberList + self.scientificOperationsList + (")",)): self.add_with_multiply,
                (".",): self.ignore
            },

            (self.scientificOperationsList + (")",)): {
                (self.simpleOperationsList + ("(", ".", "-", "", "Error", "(-", "End")): self.ignore,
                (self.numberList + self.scientificOperationsList + (")", "%")): self.add
            },

            self.numberList: {
                (self.simpleOperationsList + self.numberList + (
                    "(", ".", "-", "", "Error", "(-", "End")): self.add,
                (self.scientificOperationsList + (")", "%")): self.add_with_multiply
            },

            (".",): {
                self.numberList: self.add,
                (self.simpleOperationsList + self.scientificOperationsList + (
                    ")", "(", ".", "-", "", "Error", "(-", "End", "%")): self.ignore
            },

            ("-",): {
                (self.simpleOperationsList + ("-",)): self.switch_out,
                (self.numberList + self.scientificOperationsList + (
                    "(", ")", "", "Error", "(-", "End", "%")): self.add,
                (".",): self.ignore
            }

        }

        # For-loop used to attach all the buttons to their respective functions.
        for i in window.findChildren(QtWidgets.QPushButton):
            if i.text() == "=":
                i.clicked.connect(self.calculate)
                continue
            elif i.text() == "<--":
                i.clicked.connect(self.backspace)
                continue
            i.clicked.connect(self.button_handler)

        # Configuring the buttons in the toolbar; allows the user to switch between scientific and simple calculators.
        self.actionSimple_Calculator.triggered.connect(self.switch_to_simple)
        self.actionScientific_Calculator.triggered.connect(self.switch_to_scientific)

    def switch_to_simple(self):
        """
        Method that allows the user to switch to the simple calculator.
        """

        self.stackedWidget.setCurrentIndex(0)
        self.secondDisplay = self.secondDisplayPage1
        self.mainDisplay = self.mainDisplayPage1
        self.set_displays()

    def switch_to_scientific(self):
        """
        Method that allows the user to switch to the scientific calculator.
        """

        self.stackedWidget.setCurrentIndex(1)
        self.secondDisplay = self.secondDisplayPage2
        self.mainDisplay = self.mainDisplayPage2
        self.set_displays()

    def button_handler(self):  # once a button is clicked this function will trigger
        """
        The custom method that is attached to the majority of buttons on this calculator.
        Used to detect which button was pressed, and executes input-validation.
        """

        source_button = self.window.sender()  # function needs to know which button is pressed
        text = source_button.text()  # whatever u click will be stored here

        for key_press_set in self.validationTable:
            if text in key_press_set:
                for last_character_set in self.validationTable[key_press_set]:
                    if self.lastAllowedInput in last_character_set:  # if the character we typed is in the last char is
                        # in the set,
                        # the self validation table which we made is going to check it
                        self.validationTable[key_press_set][last_character_set](text)  # that will select those 2
                        self.set_displays()  # set display
                        return

    def switch_out(self, text, main_also=False):  # this will switch between operators if we decide to change it
        """
        Method that allows the user to switch out the last inputted character with another character.
        Only triggered in cases involving simple operations, and in special cases involving the number 0.
        """

        self.previousStates.pop()

        self.secondDisplayString = self.secondDisplayString[:-1] + f"{text}"

        if main_also:
            self.mainDisplayString = f"{text}"

        self.lastAllowedInput = f"{text}"
        self.previousStates.append(self.get_state())

    def ignore(self, text):  # it ignores invalid calculations, and it will check if it was an error
        """
        Method that ignores the user's key-press.
        Triggered when the user's input was an invalid one.
        """

        if self.lastAllowedInput in ("Error", "End"):
            self.clear(text)  # this will clear for our next calculation when we press another button again
        return

    def add(self, text):  # this is for adding every operation/numbers to the expression while inputting
        """
        Method that adds the user's input to the expression string.
        Triggered in cases where the user's input alters the expression string.
        """

        if self.lastAllowedInput in ("Error", "End"):
            self.clear(text)

        state_before_press = self.get_state()

        # Since the method of adding different characters is not as straigthforward as appending them to the
        # expression string, it was neccessary to define even more functions for the sake of a better
        # user experience while using the calculator.
        # This for-loop triggers one of the many defined functions based on the user's input.
        for possibleTexts in self.addTable:
            if text in possibleTexts:
                self.addTable[possibleTexts](text)
                break
        state_after_press = self.get_state()

        if state_before_press != state_after_press:
            self.previousStates.append(state_before_press)

    def add__number_start_end__to__number_in_exp(self):
        """
        A helper method used in the operation of recording the positions of numbers that the user
        has added to the expression string.
        Triggered in specific cases.
        """

        self.numberStartEnd.append(len(self.secondDisplayString))
        if self.pointInCurrentNumber or self.percentInNumber:
            self.numberStartEnd.append("f")
        else:
            self.numberStartEnd.append("i")

        self.numbersInExp.append(tuple(self.numberStartEnd))
        self.numberStartEnd.clear()

    def add_simple_operation(self, simple_operation):
        """
        A helper method that allows the self.add() method to correctly add any of the characters
        in the self.simpleOperationsList to the expression string.
        """

        # If the user has reached the maximum number of operations allowed, ignore their input.
        if self.operationsCount == self.operationsLimit:
            return

        if self.lastAllowedInput in (self.numberList + ("%",)) and simple_operation != "%":
            self.add__number_start_end__to__number_in_exp()

        if simple_operation == "%":
            self.percentInNumber = True
        else:
            self.percentInNumber = False
        self.pointInCurrentNumber = False
        self.lastSimpleOperationPos = len(self.secondDisplayString)

        if simple_operation == "X^y":
            self.secondDisplayString += f"^"
        else:
            self.secondDisplayString += f"{simple_operation}"

        self.lastAllowedInput = f"{simple_operation}"

        self.digitCount = 0
        self.operationsCount += 1

    def add_bracket(self, bracket):
        """
        A helper method that allows the self.add() method to correctly add the "(" and ")"
        characters to the expression string.
        """

        if bracket == "(":
            self.bracketsList.append(("(", len(self.secondDisplayString)))
        elif bracket == ")":
            if len(self.bracketsList) > 0:
                if self.lastAllowedInput in self.numberList:
                    self.add__number_start_end__to__number_in_exp()
                self.lastClosedBracketSet = self.bracketsList.pop()
            else:
                return

        self.secondDisplayString += f"{bracket}"
        self.lastAllowedInput = f"{bracket}"

    def adjust__start_end(self, after_index, amount_to_increase):
        """
        A helper method that allows the self.add_scientific_operation() method to adjust
        the recorded positions of the numbers in the self.numbersInExp list.
        """

        for i in range(len(self.numbersInExp)):
            number_set = self.numbersInExp[i]
            start, end = number_set[0], number_set[1]

            if after_index <= start:
                start += amount_to_increase
                end += amount_to_increase
                self.numbersInExp[i] = (start, end, number_set[2])

    def add_scientific_operation(self, scientific_operation):
        """
        A helper method that allows the self.add() method to correctly add any of the substrings
        in the self.scientificOperationsList to the expression string.
        """

        # If the user has reached the maximum number of operations allowed, ignore their input.
        if self.operationsCount == self.operationsLimit:
            return

        if self.lastAllowedInput in self.numberList:
            self.add__number_start_end__to__number_in_exp()

        self.percentInNumber = False
        self.pointInCurrentNumber = False
        string = self.secondDisplayString

        if self.lastAllowedInput == ")":
            index = self.lastClosedBracketSet[1]
            self.secondDisplayString = string[:index] + f"{scientific_operation}" + string[index:]

            self.adjust__start_end(index, len(scientific_operation))

            for pastState in self.previousStates:
                if self.lastSimpleOperationPos != pastState[5]:
                    self.lastSimpleOperationPos = pastState[5]
                    break
        else:
            index = self.lastSimpleOperationPos + 1
            self.secondDisplayString = string[:index] + f"{scientific_operation}(" + string[index:] + ")"

            self.adjust__start_end(index, len(scientific_operation) + 1)

        self.lastAllowedInput = f"{scientific_operation}"

        self.digitCount = 0
        self.operationsCount += 1

    def add_number(self, number):
        """
        A helper method that allows the self.add() method to correctly add any of the characters
        in the self.numbersList to the expression string.
        """

        # If the user has reached the maximum number of digits allowed in the current number, ignore their input.
        if self.digitCount == self.digitLimit:
            return

        if self.lastAllowedInput == "0":
            if number == "0":
                if len(self.secondDisplayString[self.numberStartEnd[0]:]) < 2:
                    return
            else:
                if not self.pointInCurrentNumber:
                    self.switch_out(number, True)
                    return

        if self.lastAllowedInput in (self.simpleOperationsList + ("(-", "-")):
            self.mainDisplayString = f"{number}"
        else:
            self.mainDisplayString += f"{number}"

        if self.lastAllowedInput not in (self.numberList + (".",)):
            self.numberStartEnd.append(len(self.secondDisplayString))

        self.secondDisplayString += f"{number}"
        self.lastAllowedInput = f"{number}"
        self.digitCount += 1

    def add_point(self, _):
        """
        A helper method that allows the self.add() method to correctly add the "."
        character to the expression string.
        """
        if not self.pointInCurrentNumber:
            self.pointInCurrentNumber = True
            self.secondDisplayString += "."
            self.mainDisplayString += f"."

        self.lastAllowedInput = "."

    def add_minus(self, _):
        """
        A helper method that allows the self.add() method to correctly add the "-" and "(-"
        characters to the expression string.
        """

        if self.lastAllowedInput in ("(-", "", "("):
            if self.lastAllowedInput != "(":
                self.bracketsList.append(("(", len(self.secondDisplayString)))
                self.secondDisplayString += "(-"
            else:
                self.secondDisplayString += "-"

            self.lastAllowedInput = "(-"
        else:
            self.add_simple_operation("-")

    def get_state(self):
        """
        A helper method that aids in the operation of the self.backspace() method.
        Used to record the state of the calculator everytime a variable changes,
        i.e., almost everytime the user interacts with the calculator.
        """

        return (self.secondDisplayString, self.mainDisplayString,
                self.lastAllowedInput, self.bracketsList.copy(),
                self.pointInCurrentNumber, self.lastSimpleOperationPos,
                self.digitCount, self.operationsCount,
                self.numberStartEnd.copy(), self.numbersInExp.copy(),
                self.percentInNumber)

    def add_with_multiply(self, text):
        """
        Method that adds "x(" or "x[0-9]" to the expression string.
        Triggered in specific cases (as outlined in self.validationTable.)
        """
        # so when we add in brackets and choose any other number or open bracket, it will automatically multiply the
        # next values

        if text == "(":
            self.bracketsList.append(("(", len(self.secondDisplayString) + 1))
            # we add this ( to the list and store the position of the bracket
            self.mainDisplayString = ""

        self.secondDisplayString += f"x{text}"
        self.lastAllowedInput = f"{text}"

    def backspace(self):
        """
        The custom method that is attached to the backspace ("<--") button on this calculator.
        Used to remove the last inputted character/operation.
        """

        if self.previousStates:
            (self.secondDisplayString, self.mainDisplayString, self.lastAllowedInput, self.bracketsList,
             self.pointInCurrentNumber, self.lastSimpleOperationPos, self.digitCount, self.operationsCount,
             self.numberStartEnd, self.numbersInExp, self.percentInNumber) = self.previousStates.pop()

        self.set_displays()

    def clear(self, _):
        """
        Method that is used throughout the operation of this calculator.
        Used to reset the entire state of the calculator.
        """

        self.secondDisplayString = self.mainDisplayString = self.lastAllowedInput = ""
        self.bracketsList.clear()
        self.numberStartEnd.clear()
        self.numbersInExp.clear()
        self.pointInCurrentNumber = False
        self.lastSimpleOperationPos = -1
        self.operationsCount = self.digitCount = 0

        self.previousStates = []

    def calculate(self):
        """
        The method in which the actual calculation of the user's input takes place.
        This method is attached to the equal-to (=) button of the calculator.
        """

        # If the expression string is in an incomplete state, give a generic "Error".
        if self.lastAllowedInput in (self.simpleOperationsList + ("(", ".", "-")) or len(self.bracketsList) > 0:
            # if the last character of our inputs is in the operations list or if the brackets in incomplete then it
            # will show error
            self.mainDisplayString = "Error"
            self.lastAllowedInput = "Error"
            self.secondDisplayString = ""

        # In case the user presses the "=" button right after a successful/unsuccessful calculation.
        elif self.lastAllowedInput in ("End", "Error"):
            # this condition will satisfy when the calculation has added properly,
            # when we press equal to again after calculation, it will do nothing.
            return

        else:

            if len(self.numberStartEnd) != 0:  # if this is not empty
                self.add__number_start_end__to__number_in_exp()
                # then add it to this expression, the left out
                # position of the last digit to prevent error

            expression = self.secondDisplayString.replace("x", "*")
            # * is the multiplication operator, whereas /100 is
            # percent formula

            offset = 0  # this is the position of the calculation in the label, the numbers entered will shift
            # because of the custom class, to prevent
            # this we must increment it by 5 or 7 for Int and Float respectively
            for start, end, numberType in self.numbersInExp:
                if numberType == "i":
                    expression = (expression[:(start + offset)] +
                                  "Int(" +
                                  expression[(start + offset):(end + offset)] +
                                  ")" +
                                  expression[(end + offset):])
                    offset += 5
                elif numberType == "f":
                    expression = (expression[:(start + offset)] +
                                  "Float(" +
                                  expression[(start + offset):(end + offset)] +
                                  ")" +
                                  expression[(end + offset):])
                    offset += 7

            expression = expression.replace("%", "/100")
            for i, j in (("Sin^(-1)", "math.asin"), ("Cos^(-1)", "math.acos"), ("Tan^(-1)", "math.atan"),
                         ("Sin", "math.sin"), ("Cos", "math.cos"), ("Tan", "math.tan"),
                         ("Sqrt", "math.sqrt"), ("Log", "math.log10"), ("x", "*"), ("%", "/100"),
                         ("^", "**")):
                expression = expression.replace(i, j)  # this is assigning the math functions

            try:
                answer = round(eval(expression),
                               self.answerDecimalLimit)  # rounds the values to 10th decimal place max
                if answer < 0:
                    self.secondDisplayString += f" = ({answer})"  # if our answer from calculation is negative then
                    # it will be wrapped in ()
                else:
                    self.secondDisplayString += f" = {answer}"  # else print it out normally

                self.mainDisplayString = f"{answer}"  # bigger box will display the answer
                self.lastAllowedInput = "End"
            except Exception as e:
                self.mainDisplayString = f"{str(e).upper()}"  # unless if the calculations are wrong, like the way we
                # calculate then it's an error
                self.lastAllowedInput = "Error"
                self.secondDisplayString += " = Error"

        self.set_displays()

    def set_displays(self):
        # we are setting our string values which was done in except and elsewhere, here.
        self.secondDisplay.setText(self.secondDisplayString)
        self.mainDisplay.setText(self.mainDisplayString)

# setting up the application and running it
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = Calculator(MainWindow)

MainWindow.show()
app.exec_()
