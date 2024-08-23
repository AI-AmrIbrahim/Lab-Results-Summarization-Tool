# %% Imports
from google.cloud import bigquery
import pandas as pd
import io
from retrying import retry
import random

# Gemini
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models


# %% Extract formated string from BigQuery Query
def query_str_extract(query_job):
    """
    Extracts data from a BigQuery query result into a string for singular analysis.

    Args:
        query_job: The result of a BigQuery query.

    Returns:
        A string containing the extracted data in pipe delimted format (columns: Component, Component Base, New Value, New Flag) preceded by age and sex.
    """
    for ind, row in enumerate(query_job):
        # Extracting result age and sex since those are constants and adding column names for pipe delimeted data format
        if ind == 0:
            age, sex = row[0:2]
            data_string = f"Age: {age}\n"
            data_string += f"Sex: {sex}\n"
            data_string += "Component|Component_Base|New_Value|New_Flag\n"
        # Extract component, component base, new value, new flag to be fed into pipe delimeted format
        component, component_base, val, result_flag = row[2:6]
        data_string += f"{component}|{component_base}|{val}|{result_flag}\n"
    return data_string


def query_str_extract_comp(query_job):
    """
    Extracts and formats component data for comparative analysis from a query job.

    Args:
        query_job: A list of rows representing the query job data. Each row is a list of values.

    Returns:
        A string containing the formatted component data.
    """
    for ind, row in enumerate(query_job):
        # Extracting result age and sex since those are constants and adding column names for pipe delimeted data format
        if ind == 0:
            age, sex = row[0:2]
            data_string = f"Age: {age}\n"
            data_string += f"Sex: {sex}\n"
            data_string += "Component|Component_Base|Initial_Value|Initial_Flag|New_Falue|New_Flag\n"
        # Extract component, component base, new value, new flag, intial value, initial flag to be fed into pipe delimeted format
        component, component_base, init_val, init_flag, new_val, new_flag = row[2:8]
        data_string += f"{component}|{component_base}|{init_val}|{init_flag}|{new_val}|{new_flag}\n"
    return data_string


# %% Add important specific tests to string if it doesnt exit (HGBA1c)
def add_a1c(data_string: str):
    """
    Adds Hemoglobin A1c to the provided data string if it doesn't already exist.

    Args:
        data_string: A string containing the data, including age, sex, and component data in pipe delimeted format.

    Returns:
        A string containing the updated data with Hemoglobin A1c added if necessary.
    """
    # Split the data into its sections age, sex, pipe delim data
    age, sex, data_lab = data_string.split("\n", 2)
    # Convert the data into data frame
    data_stream = io.StringIO(data_lab)
    df = pd.read_csv(data_stream, sep="|")
    # Check for A1c is in component base
    if df["Component_Base"].str.contains("HGBA1C").any():
        data_string_aug = df.to_csv(sep="|", index=False)
    else:
        # Get column names
        col_names = list(df.columns)
        # Create a data frame with HGBA1C
        df2 = pd.DataFrame(
            [
                [
                    "HEMOGLOBIN A1C",
                    "HGBA1C",
                    "Not Recorded",
                    "Not Recorded",
                    "Not Recorded",
                    "Not Recorded",
                ]
            ],
            columns=col_names,
        )
        # Concatenate the data frames
        df_concat = pd.concat([df2, df])
        # Convert data frame back into pipe delimeted string
        data_string_aug = df_concat.to_csv(sep="|", index=False)

    return "\n".join([age, sex, data_string_aug])


# %%% Prepend ask statement to formated data string ??? deal with query_job
def prepend_ask(query_job, comparative: bool = False):
    """
    This function takes a query job and returns a string that includes an ask statement and the data extracted from the query job.

    Args:
        query_job: A list of rows representing the query job data. Each row is a list of values.
        comparative: A boolean value indicating whether the analysis is comparative.

    Returns:
        A string containing the ask statement and the data extracted from the query job.
    """
    # Condition for single or comaprative analysis
    if not comparative:
        data_string = query_str_extract(query_job)
        return (
            "Using only the data in the most recent lab work, compose a care plan for the following lab work, providing:(1) an overview of lab results and their consequences (2) a preventative care plan (3) follow-up instructions\n"
            + data_string
        )  # Return the ask statement before the data to be clear
    else:
        # If HGBA1C is not within a patient's labwork add an empty HGBA1C row
        data_string = add_a1c(query_str_extract_comp(query_job))
        return (
            "Using only the data within the lab tests, compare the initial and new lab test values for each test. Note any changes in test values and their potential causes. Based on your analysis, compose a care plan for the patient, including:\n1. An overview of lab results:\n\t1a. Comparisons: Highlight any significant changes between the initial and new lab values.\n\t1b. Other notable lab values: Discuss any other lab values that are outside the normal range and their potential consequences.\n2. A preventative care plan: Recommend specific actions the patient can take to prevent future health issues based on their lab results.\n3. Follow-up instructions: Outline the next steps for the patient, including any additional tests, medication adjustments, or specialist referrals that may be necessary.\n\n"
            + data_string
        )  # Return the ask statement before the data to be clear


# %% Manually patch missing data in provided example data
def manual_patch(data_lab: str, comp_val_flag: dict):
    """
    This function takes a pipe-delimited data string and a dictionary of component base: [values, initial flag values],
    and returns a pipe-delimited data string with the initial value and initial flag columns populated for each component base.

    Args:
        data_lab (str): A pipe-delimited data string.
        comp_val_flag (dict): A dictionary where the keys are component base and the values are tuples of
            the form (initial_value, initial_flag).

    Returns:
        str: A pipe-delimited data string with the initial value and initial flag columns populated for each component base.
    """
    # Convert the data into data frame
    data_stream = io.StringIO(data_lab)
    df = pd.read_csv(data_stream, sep="|")
    # Add Intial Value and Initial Flag columns
    df.insert(2, "Initial_Value", "Not Recorded")
    df.insert(3, "Initial_Flag", "Not Recorded")
    # Loop through component_bases and ini_val_flag to manually path data
    # To manually patch (1) Get index for component base (2) Add value for inital value and flag
    for comp, val_flag in comp_val_flag.items():
        index = df.index[df["Component_Base"] == str(comp)].tolist()[0]
        df.loc[index, ["Initial_Value", "Initial_Flag"]] = val_flag
    # Return pipe delimeted data string
    return df.to_csv(sep="|", index=False)


# %% Format all examples based on type of analysis ??? rm phi
def example_format(comparative: bool = False):
    """
    Generates example inputs and outputs for the care plan generation model.

    Args:
        comparative: Whether to generate examples for comparative analysis.

    Returns:
        A tuple containing two lists:
            - inputs: A list of example input strings.
            - outputs: A list of example output strings.
    """
    # Example statements for clarity
    exp_input = "Example input\n"
    exp_output = "Example output\n"

    if not comparative:
        # Single analysis example
        with open("Examples/data3.txt", "r") as f:
            data = f.read().strip()
        data = exp_input + data + "\n"
        # add comment
        with open("Examples/letter3.txt", "r") as f:
            letter = f.read().strip()
        letter = exp_output + letter

        examples = data + letter

    else:
        # Comparative analysis examples
        with open("Examples/data1.txt", "r") as f:
            data1 = f.read().strip()
        with open("Examples/data2.txt", "r") as f:
            data2 = f.read().strip()

        # Adjust asks for comparative analysis and manually patching missing data
        # Split the data into its sections age, sex, pipe delim data
        _, age1, sex1, data1_lab = data1.split("\n", 3)
        _, age2, sex2, data2_lab = data2.split("\n", 3)
        # Change ask from singular analysis ask to comparative analysis ask
        ask = "Using only the data within the lab tests, compare the initial and new lab test values for each test. Note any changes in test values and their potential causes. Based on your analysis, compose a care plan for the patient, including:\n1. An overview of lab results:\n\t1a. Comparisons: Highlight any significant changes between the initial and new lab values.\n\t1b. Other notable lab values: Discuss any other lab values that are outside the normal range and their potential consequences.\n2. A preventative care plan: Recommend specific actions the patient can take to prevent future health issues based on their lab results.\n3. Follow-up instructions: Outline the next steps for the patient, including any additional tests, medication adjustments, or specialist referrals that may be necessary.\n\n"
        # Construct dict with component base and its respective initial value and flag
        comp_val_flag1 = {
            "GLUCOSE": [122, "High"],
            "HGBA1C": [6.2, "High"],
            "LDLCALC": [81, "Normal"],
        }

        data_string1 = manual_patch(data1_lab, comp_val_flag1)
        data1 = "\n".join([exp_input, ask, age1, sex1, data_string1])

        comp_val_flag2 = {"HGBA1C": [5.7, "High"]}

        data_string2 = manual_patch(data2_lab, comp_val_flag2)
        data2 = "\n".join([exp_input, ask, age2, sex2, data_string2])

        # Add specific examples to give a general guideline
        # (1) No initial & high flag [done]
        # (2) No initial & low flag [done]
        # (3) No initial & normal flag [done]
        # (4) Value remains the same & low flag [done]
        # (5) Value remains the same & high flag [done]
        # (6) Value remains the same & normal flag [done]
        # (7) increase in value & no flag [done]
        # (8) increase in value & low flag [done]
        # (9) increase in value & high flag [done]
        # (10) decrease in value & high flag [done]
        # (11) decrease in value & low flag
        # (12) decrease in value & normal flag
        # (13) normal flag to high flag
        # (14) normal flag to low flag
        # (15) low flag to normal flag
        # (16) high flag to normal flag
        # (17) value within normal range ie no flag [this might not be necessary since Physician inputs range]
        # (18) value outside normal range ie high/low flag [this might not be necessary since Physician inputs range]

        spc_exp = (
            ask
            + "Component|Component_Base|Initial_Value|Initial_Flag|New_Value|New_Flag\r"
        )
        spc_exp += """
A|A|Not Recorded|Not Recorded|27|High\r
B|B|Not Recorded|Not Recorded|1.2|Low\r
C|C|Not Recorded|Not Recorded|5|Normal\r
D|D|0.8|Low|0.8|Low\r
E|E|100|High|100|High\r
F|F|3.2|Normal|3.2|Normal\r
G|G|5.2|Normal|5.6|Normal\r
H|H|51|Low|53|Low\r
I|I|7|High|9|High\r
J|J|243|High|230|High\r
K|K|381|High|293|Normal\r
L|L|123|Low|141|Normal\r
"""
        spc_out = """
Overview of Your Recent Lab Results:\n
Your A is high at 27, the normal range for A is [insert normal range here]. A is ... .\n
Your B is low at 1.2, the normal range for B is [insert normal range here]. B is ... .\n
Your D remains low at 0.8, the normal range for D is [insert normal range here]. D is ... .\n
Your E remains high at 100, the normal range for E is [insert normal range here]. E is ... .\n
Your G increased from 5.2 to 5.6 however remains within range of normal. G is ... .\n
Your H increased from 51 to 53 however remains low, the normal range for H is [insert normal range here]. H is ... .\n
Your I increased from 7 to 9 however remains high, the normal range for I is [insert normal range here]. I is ... .\n
Your J decreased from 243 to 230 but remains high, the normal range for J is [insert normal range here]. J is ... .\n
Your K decreased from 381 to 293 placing you within the range of normal. K is ... .\n
Your L increased from 123 to 141 placing you within the range of normal. L is ... .\n
"""

        # Read Dr. Young's comparative example outputs
        with open("letter1.txt", "r") as f:
            letter1 = f.read().strip()
        with open("letter2.txt", "r") as f:
            letter2 = f.read().strip()
        # Prepend example output statement "Example output" for clarity
        letter1 = "\n".join([exp_output, letter1, "\n"])
        letter2 = "\n".join([exp_output, letter2, "\n"])
        # Construct examples string
        examples = "\n".join(
            [data1, letter1, data2, letter2, exp_input, spc_exp, exp_output, spc_out]
        )

    return examples


# %% Gemini-1.5 Pro Prompting Function
# Sometimes due to saftey settions content would not have text generated therefore if an error occurs it would rerun the function up to 3 times
@retry(stop_max_attempt_number=3, wait_fixed=0)
# Function to extract BigQuery data into Patient Care Plan using Gemini-1.5 Pro
def prompt_fun_gemini(
    query_job,
    comparative: bool = False,
    max_tokens: int = 3000,
    temp: float = 0,
    topP: float = 0.15,
):
    """
    This function takes a patient ID, a sequence of revisions, and optional parameters to generate a care plan report using Gemini-1.5 Pro-001.

    Args:
        query_job: A list of rows representing the query job data. Each row is a list of values.
        comparative: A boolean value indicating whether the analysis is comparative.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 1000.
        temp (float, optional): The temperature parameter for the language model. Defaults to 0.1.
        topP (float, optional): The top_p parameter for the language model. Defaults to 0.45.
        topK (int, optional): The top_k parameter for the language model. Defaults to 25.

    Returns:
        str: The generated care plan report.
    """
    # Initiate Gemini-1.5 LLM
    Project = '[Insert Vertex AI Project Here]'
    Loc = '[Insert Project Location Here]'
    vertexai.init(project=Project, location=Loc)
    model = GenerativeModel(
        "gemini-1.5-pro-001",
    )

    # Prompt context which includes (1) Role of PCP and function to generate Care Plan (2) Structure of Care plan (3) Other guidelines regarding examples, data, and text
    context = """You are an established primary care physician who believes in the importance of preventative care. Given the recent blood work and checkup, you want to provide patients with a comprehensive overview of their health and offer personalized preventative care recommendations.

    Based on the information extracted from patient's latest checkup, including their age, sex, major comorbidities (if any), BMI, and blood work lab values, you will compose a letter with the following sections:

    Start the letter with a friendly greeting
    Overview of Lab Results: Briefly summarize the key findings from the blood work and any other relevant tests. Please highlight any abnormalities or areas of concern with respect to flag indicators. Do not use inflammatory wording like "significant increase" or "significant decrease" instead use "increase" or "decrease". Ask the physician to insert normal values for the patient's sex and age as "[Insert normal range here]".
    Preventative Care Plan: Provide specific recommendations for preventative care based on the patient's individual needs and risk factors. This may include lifestyle modifications and medications. Do not provide referral recommendations.
    Follow-up: Indicate if any further follow-up is necessary, such as additional testing, medication adjustments, or scheduling an appointment for further discussion.
    End the letter with a friendly closing, reminding the patient that you are available to answer any questions they may have.

    Use only the information provided.
    Only use reputable medical sources for your concerns output.
    Utilize headers, bold text, and bullet points to make the letter easy to read and understand.
    Do not use example inputs in generating care plan.
    Use the outline and structure of example outputs as reference when generating care plan.\n
    """
    prompt = context

    # Append appropriate examples based on if the user conducts singular (seq_rev2 = None) or comparative analysis
    if not comparative:
        examples = example_format(comparative=False)
        filename = f"singular_analysis_output.txt"
    else:
        examples = example_format(comparative=True)
        filename = f"comparative_analysis_output.txt"

    prompt += (
        examples + "\ninput:\n" + prepend_ask(query_job, comparative) + "\noutput:\n"
    )

    # Gemini-1.5 configuration for max tokens, temperature, and topP
    generation_config = {
        "max_output_tokens": max_tokens,
        "temperature": temp,
        "top_p": topP,
    }

    # Safety settings set to BLOCK_NONE to limit errors
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    }

    # Prompt LLM to generate response
    responses = model.generate_content(
        [prompt],
        generation_config=generation_config,
        #   safety_settings=safety_settings,
    )

    # Return respoonse object
    return responses # reposeonse.text to get the text output
