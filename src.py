import os
import re
import unicodedata
import pandas as pd

from pypdf import PdfReader


def unicodeToAscii(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def remove_indian_letters(text):
    # Define the pattern to match Indian letters
    indian_letters_pattern = re.compile(r"[\u0900-\u097F]+")

    # Replace Indian letters with space
    cleaned_text = indian_letters_pattern.sub("|", text)

    return cleaned_text


def remove_non_printable(text):
    # Define the pattern to match non-printable characters
    non_printable_pattern = re.compile(r"[\x00-\x1F\x7F-\x9F]")

    # Replace non-printable characters with an empty string
    cleaning_text = non_printable_pattern.sub("", text)

    delete_chars = "".join(
        chr(i) for i in range(32)
    )  # Create a string of all non-printable characters (ASCII 0-31)
    translation_table = str.maketrans(
        "", "", delete_chars
    )  # Create a translation table to remove those characters
    cleaned_text = cleaning_text.translate(translation_table)

    return cleaned_text


def remove_non_ascii_letters(text):
    # Define the pattern to match ASCII letters not in the range [32, 127]
    non_ascii_pattern = re.compile(r"[^\x00-\x7E]")

    # Replace non-ASCII letters with an empty string
    cleaned_text = non_ascii_pattern.sub("", text)

    return cleaned_text


def normalize_text(text):  # for Log Printing...
    lines = [
        " ".join(filter(len, line.split())) for line in text.split("\n") if line.strip()
    ]
    text = " ".join(lines)
    text = unicodeToAscii(text)
    text = text.replace("’", "'")
    text = remove_indian_letters(text)
    text = remove_non_printable(text)
    result = remove_non_ascii_letters(text)
    result = result.replace("( ", "(")
    result = result.replace(" )", ")")
    return result


def get_content(file_path):
    """
    This function attempts to extract text content from a PDF file using PyPDF (if available).

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: The extracted text content from the PDF file (if successful).

    Raises:
        ValueError: If the provided file path does not exist or is not a PDF file.
        ImportError: If the PyPDF library is not found.
    """

    # Check if file exists and has .pdf extension
    if not os.path.exists(file_path) or not file_path.lower().endswith(".pdf"):
        raise ValueError(f"Invalid file path '{file_path}'")

    try:
        # creating a pdf reader object
        reader = PdfReader(file_path)
    except ImportError:
        raise ImportError(
            "pypdf library not found. Please install it using 'pip install pypdf' (if available)."
        )
    except FileNotFoundError:
        raise ValueError(f"PDF file not found at '{file_path}'")

    # Extract text from all pages (might not be reliable)
    text_content = ""
    for page in reader.pages:
        # Text extraction using getPage().extractText() (limited capabilities)
        text_content += page.extract_text() + "\n"

    # Return the extracted text content (might be incomplete)
    return normalize_text(text_content)


def get_value_by_key(input_string, key):
    # Split the input string using the '|' delimiter
    parts = input_string.split("|")

    # Iterate over the parts to find the key and corresponding value
    for part in parts:
        # Check if the key is present in the current part
        if key in part:
            # Extract the value corresponding to the key
            # by removing the key itself and any leading/trailing whitespace
            value = part.replace(key, "").strip()
            return value

    # If the key is not found, return None or raise an exception
    return None


def get_answer(file_path):
    content = get_content(file_path)

    keys = [
        "(Candidate's Name)",
        "(Email Address)",
        "(State)",
        "(Mobile Number)",
        "(Emergency Mobile Number)",
    ]

    answers = [get_value_by_key(content, key) for key in keys]
    return answers


INPUT_DIR = "./INPUT/"
OUTPUT_DIR = "./OUTPUT/"

if __name__ == "__main__":
    if not os.path.exists(INPUT_DIR):
        print(
            "Input directory not exists! Please check out the name and then try again! : 'INPUT'"
        )
        exit(0)

    print("Started!")

    # Check if the output directory already exists
    if not os.path.exists(OUTPUT_DIR):
        # If it doesn't exist, create the directory
        os.makedirs((OUTPUT_DIR))

    # Get a list of all files in the directory
    files = os.listdir(INPUT_DIR)

    total_count = 0
    success = 0
    failed = 0
    total_result = []

    # Loop through each file in the directory
    for file_name in files:
        # Check if the file is a regular file (not a directory)
        real_name = os.path.join(INPUT_DIR, file_name)
        if os.path.isfile(real_name) and real_name.lower().endswith(".pdf"):
            total_count = total_count + 1
            # Open and read the file
            print(f"Working on ... {real_name}")

            one_result = get_answer(real_name)
            one_result.append(file_name)

            total_result.append(one_result)

            if None in one_result:
                failed = failed + 1
            else:
                success = success + 1

    columns = [
        "(Candidate's Name)",
        "(Email, Address)",
        "(State)",
        "(Mobile Number)",
        "(Emergency Mobile Number)",
        "File_Name (Optional)",
    ]

    for i in range(len(total_result)):
        total_result[i][3] = f"[ {total_result[i][3]} ]"
        total_result[i][4] = f"[ {total_result[i][4]} ]"

    # Create DataFrame with index starting from 1
    df = pd.DataFrame(
        total_result, columns=columns, index=range(1, len(total_result) + 1)
    )

    # # Convert all columns to strings
    # df = df.astype(object)

    # text_cols = [
    #     "(Mobile Number)",
    #     "(Emergency Mobile Number)",
    # ]  # Replace with your actual column names
    # df[text_cols] = df[text_cols].astype(
    #     object
    # )  # Convert specific columns to object type (text)

    # Write DataFrame to CSV file
    df.to_csv(f"{OUTPUT_DIR}output.csv", index=True)

    print("Result Saved!")
    print(f"Total : {total_count}")
    print(f"Success : {success}")
    print(f"Faild : {failed}")
