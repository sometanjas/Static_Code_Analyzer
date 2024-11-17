import re
import sys, os
import logging
import ast


class Logger:
    # STEP 1
    # create a logger object instance
    logger = logging.getLogger()

    # STEP 2
    # specify the lowest boundary for logging
    logger.setLevel(logging.DEBUG)

    # STEP 3
    # set a destination for your logs or a handler
    # here, we choose to print on console (a console handler)
    console_handler = logging.StreamHandler()

    # STEP 4
    # set the logging format for your handler
    log_format = '%(asctime)s | %(levelname)s: %(message)s'
    console_handler.setFormatter(logging.Formatter(log_format))

    # finally, add the handler to the logger
    logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


logger = Logger()


class TooLong(Exception):
    def __init__(self, line_number):
        self.line_number = line_number

    def __str__(self):
        return f"Line {self.line_number}: S001 Too long"


class Indentation(Exception):
    def __init__(self, line_number):
        self.line_number = line_number

    def __str__(self):
        return f"Line {self.line_number}: S002 Indentation is not a multiple of four"


class Semicolon(Exception):
    def __init__(self, line_number):
        self.line_number = line_number

    def __str__(self):
        return f"Line {self.line_number}: S003 Unnecessary semicolon"


class Spaces(Exception):
    def __init__(self, line_number):
        self.line_number = line_number

    def __str__(self):
        return f"Line {self.line_number}: S004 Less than two spaces before inline comments"


class Todo(Exception):
    def __init__(self, line_number):
        self.line_number = line_number

    def __str__(self):
        return f"Line {self.line_number}: S005 TODO found"


class Blank(Exception):
    def __init__(self, line_number):
        self.line_number = line_number

    def __str__(self):
        return f"Line {self.line_number}: S006 More than two blank lines used before this line"


class SpacesAfterClass(Exception):
    def __init__(self, line_number, construction_name):
        self.line_number = line_number
        self.construction_name = construction_name

    def __str__(self):
        return f"Line {self.line_number}: S007 Too many spaces after {self.construction_name}"


class ClassName(Exception):
    def __init__(self, line_number, class_name):
        self.line_number = line_number
        self.class_name = class_name

    def __str__(self):
        return f"Line {self.line_number}: S008 Class name {self.class_name} should be written in CamelCase"


class FunctionName(Exception):
    def __init__(self, line_number, function_name):
        self.line_number = line_number
        self.function_name = function_name

    def __str__(self):
        return f"Line {self.line_number}: S009 Function name {self.function_name} should be written in snake_case"


def check_length(line, line_number):
    if len(line.rstrip()) > 79:
        raise TooLong(line_number)


def check_todo(line, line_number):
    if '#' in line:
        comment_part = line.split('#', 1)[1]  # Get everything after the first #
        if 'TODO' in comment_part.upper():
            raise Todo(line_number)


def check_semicolon(line, line_number):
    if re.search(r"(.*)(;(\s)*#|;$)", line) and not re.search(r"#.*;", line):
        raise Semicolon(line_number)


def check_indentation(line, line_number):
    leading_spaces = len(line) - len(line.lstrip(' '))
    if leading_spaces % 4 != 0:
        raise Indentation(line_number)


def check_spaces(line, line_number):
    # Find the position of the first `#` in the line
    comment_start = line.find('#')

    # If there is a `#` and it's not at the very beginning of the line
    if comment_start > 0:
        # Check if there are exactly two spaces before the first `#`
        preceding_text = line[:comment_start]
        if not re.search(r"  $", preceding_text):  # Ensures exactly two spaces before `#`
            raise Spaces(line_number)


def check_blanks(line, line_number, blank_line_count):
    if line.strip() == "":
        blank_line_count += 1
    else:
        # If more than two blank lines were encountered before this non-blank line, raise an error
        if blank_line_count > 2:
            raise Blank(line_number)
        # Reset the blank line count as we hit a non-blank line
        blank_line_count = 0
    return blank_line_count


def check_spaces_after_class(line, line_number):
    pattern = r"^(class|def)(?: {0}| {2,})\w"
    line = line.strip()
    match = re.search(pattern, line)
    if match:
        raise SpacesAfterClass(line_number, match.group(1))


def check_class_name(line, line_number):
    if not line.startswith("class"):
        return
    class_name = line[6:]
    class_name = class_name[:-2]
    if class_name[0].islower():
        raise ClassName(line_number, class_name)


def check_function_name(line, line_number):
    line = line.strip()
    if not line.startswith("def"):
        return
    function_name = line[4:]
    function_name = function_name[:-2]
    if function_name[0].isalpha() and function_name[0].isupper():
        raise FunctionName(line_number, function_name)


def code_analyzer(read, file_path):
    blank_line_count = 0
    for line_number, line in enumerate(read, start=1):
        checks = [check_length, check_indentation, check_semicolon, check_spaces, check_todo]
        for checker in checks:
            try:
                checker(line, line_number)
            except (TooLong, Indentation, Semicolon, Spaces, Todo) as e:
                print(f"{file_path}: {e}")
        # Check for blank lines, updating the blank line count
        try:
            blank_line_count = check_blanks(line, line_number, blank_line_count)
        except Blank as e:
            blank_line_count = 0
            print(f"{file_path}: {e}")

        new_checkers = [check_spaces_after_class, check_class_name, check_function_name]
        for new_checker in new_checkers:
            try:
                new_checker(line, line_number)
            except (SpacesAfterClass, ClassName, FunctionName) as e:
                print(f"{file_path}: {e}")


SNAKE_CASE_PATTERN = re.compile(r'^[a-z_][a-z0-9_]*$')


def is_snake_case(name):
    return bool(SNAKE_CASE_PATTERN.match(name))


class Analyzer(ast.NodeVisitor):

    def __init__(self):
        self.errors = []

    def visit_FunctionDef(self, node):
        # S010: Argument name should be written in snake_case
        for arg in node.args.args + node.args.kwonlyargs:
            if not is_snake_case(arg.arg):
                self.errors.append((node.lineno, 'S010', f"Argument name '{arg.arg}' should be written in snake_case"))

        # S012: Default argument value is mutable
        for default in node.args.defaults + node.args.kw_defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.errors.append((node.lineno, 'S012', "Default argument value is mutable"))

        self.generic_visit(node)

    def visit_Name(self, node):
        # S011: Variable name should be written in snake_case
        if isinstance(node.ctx, ast.Store) and not is_snake_case(node.id):
            self.errors.append((node.lineno, 'S011', f"Variable name '{node.id}' should be written in snake_case"))

        self.generic_visit(node)


def analyze_code(code):
    tree = ast.parse(code)
    analyzer = Analyzer()
    analyzer.visit(tree)
    return analyzer.errors


def read_file(file_path):
    try:
        with open(file_path, "r") as file:
            read = file.readlines()
            code_analyzer(read, file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    try:
        with open(file_path, "r") as file:
            test_code = file.read()
            errors = analyze_code(test_code)
            for error in errors:
                print(f"{file_path}: Line {error[0]}: {error[1]} {error[2]}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")


def read_directory(directory_path):
    try:
        files = [filename for filename in os.listdir(directory_path) if
                 os.path.isfile(os.path.join(directory_path, filename))]
        logger.info(f"Created a list from files in a directory")
        files.sort()
        logger.info(f"Sorted list of files in the directory in ascending order according to the file name")
        for filename in files:
            file_path = os.path.join(directory_path, filename)
            # Only process files, skip directories
            if os.path.isfile(file_path):
                read_file(file_path)
    except Exception as e:
        print(f"Error reading directory {directory_path}: {e}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python code_analyzer.py directory-or-file")
        sys.exit(1)

    file_path = sys.argv[1]

    if os.path.isdir(file_path):
        logger.info(f"The provided path is a directory")
        read_directory(file_path)
    elif os.path.isfile(file_path):
        logger.info(f"The provided path is a file")
        read_file(file_path)
    else:
        print(f"The path '{file_path}' is neither a valid file nor directory.")


if __name__ == "__main__":
    main()
