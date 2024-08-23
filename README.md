# Lab Results Summarization Tool

Over the summer of 2024, I interned at Hackensack Meridian Health (HMH) on the Data Science team. The project I worked on during my internship was the development of a Lab Results Summarization Tool. This tool leverages Vertex AI using Google's Gemini-1.5 Pro model to generate summarized documents from patients' most recent lab results.

## Objective and Impact

The goal of the tool was to streamline communication between physicians and patients by summarizing complex lab results into a clear and actionable document. The document produced by the tool was divided into three key sections:

1. **Overview of Lab Results:** This section highlighted all lab tests that showed alarming results and tracked both positive and negative changes compared to the patient's previous lab work.
2. **Preventative Care Plan:** Based on the lab results, this section provided lifestyle recommendations aimed at improving the patient's overall health.
3. **Follow-Up Instructions:** This section reminded patients to schedule their next appointment and encouraged them to reach out with any questions or concerns.

The Lab Results Summarization Tool was designed to save physicians time by automating the process of summarizing and communicating lab results. By providing a clear, easy-to-understand summary, the tool helped bridge the gap between complex medical data and patient understanding, ultimately improving the overall patient experience. Using this tool can save up to 4 hours of the physician's time that can be dedicated to their patients.

## Data

Data was obtained from HMH's Electronic Medical Records (EMR) through BigQuery. Data gathered included patient details including age, sex, the most recent two lab results, and BMI.

## Data Parsing

The extracted data was then formatted into a pipe-delimited format, making it easier for the Large Language Model (LLM) to parse and understand the inputs, ensuring that all relevant information was processed efficiently. Overview of the format:

```
Age:
Sex:
Component|Component_Base|Initial_Value|Initial_Flag|New_Value|New_Flag
```

## Prompt Engineering

This tool performs two types of analysis: singular and comparative:

* **Singular analysis:** The most recent lab result is passed to the LLM. The LLM then highlights the most alarming lab results.
* **Comparative analysis:** The two most recent lab results are passed to the LLM. The LLM then highlights any significant changes between the initial and new lab tests and highlights other alarming lab results.

### Context

* The initial prompt given to the model was simple: "You are an established Primary Care Physician who cares about preventative care." While this provided a basic context for generating the lab summaries, it did not yield the level of detail or precision needed.
* Through a process of trial and error, the prompt was refined to include more specific instructions. The final prompt evolved into a multi-layered context that defined the role of the model as a Primary Care Physician committed to preventative care. It also provided structured instructions on how the document should be organized, specifying the three key sections (Overview, Preventative Care Plan, and Follow-Up Instructions). Additionally, guidelines were added to reference example outputs for maintaining consistent style and tone across the generated documents. This refined prompt significantly improved the model's ability to produce coherent and actionable summaries.

### Model Selection

* **MedLM:** Initially, I utilized the MedLM model to generate lab summaries. While MedLM produced some promising outcomes, it frequently missed important data and generated hallucinations that compromised the reliability of the summaries.
* **Gemini-1.5 Pro:** After consulting with a Google AI Customer Engineer, I switched to the Gemini-1.5 Pro model. This model significantly improved the accuracy of the generated summaries, reducing hallucinations and more reliably capturing the data provided. Additionally, I incorporated specific examples to handle edge cases, which further enhanced the model's generative capabilities.

### Learning Methods

* **Zero-shot:** I began the modeling process with zero-shot learning, where the AI model was tasked with generating summaries without any prior examples. Unfortunately, this approach did not yield satisfactory results. The model's summaries were often incomplete and failed to emphasize the critical lab results that required attention.
* **Few-shot:** To improve the model's performance, I introduced few-shot learning by supplying three examples of notes previously sent by a doctor to her patients. These examples served as a guide for the model in generating similar summaries. However, this approach introduced a bias toward comparing the two most recent lab results, leading to inadequate handling of cases where only the latest lab work needed to be summarized.
* **Redefined Few-shot:** To address the bias observed in the few-shot learning model, I implemented a refined approach where different examples were passed depending on the user's request. Comparative examples were used when two lab works were being compared, and singular examples were provided when the focus was solely on the most recent lab results. This adjustment allowed the model to better tailor its responses to specific user needs, balancing both singular and comparative analysis.

### Example Formatting

All examples are formatted to be very direct with the LLM before supplying an input 'Example input' and before an example output 'Example output':

```
Example input:
...
Example output:
...
```

#### Provided Examples

As mentioned earlier, three reports sent out by a primary care physician were provided as [examples](Examples). Extracting the associated patient EMR data associated with each report. I utilized the three reports and respective data as examples for the LLM.

#### Edge Case Examples

Additionally, edge case examples were added for the comparative analysis case to get the most optimal output formatting for each respective edge case. Some edge cases include:

```
Example input:

Component|Component_Base|Initial_Value|Initial_Flag|New_Value|New_Flag
A|A|Not Recorded|Not Recorded|27|High
B|B|0.8|Low|0.8|Low
C|C|5.2|Normal|5.6|Normal
D|D|243|High|230|High

Example output:

Your A is high at 27, ... .
Your B remains low at 0.8, ... .
Your C increased from 5.2 to 5.6 however remains within range of normal, ... .
Your D decreased from 243 to 230 but remains high, ... .
```

## Demo

Due to PHI, there is no EMR data that can be queried using this repository, therefore I included a [demo](Demo) showcasing tool functionality with sample input and output.

## Stakeholder Feedback

This tool was showcased to two physician stakeholders. The feedback was overall positive "80% of the work is done" - Stakeholder 1. I categorized other feedback as must-haves and nice-to-haves:

* **Must Haves:**
    * Avoid use of inflammatory statements
    * Avoid referrals to other departments and/or physicians
* **Nice to Haves:**
    * Add clinical normal ranges into the LLM
    * Add medication recommendations based on patient needs
    * Add vaccination recommendations based on patient needs and vaccination history

## Future Enhancements

* Prompt engineering optimization using DSPy
* Passing clinical ranges into the LLM either:
    * Passing the ranges into the LLM
    * Adding clinical ranges as flags into EMR
* Asking stakeholders for test importance or hierarchy:
    * Individual
    * Coupling of tests
* Pipeline to auto-add approved documents into examples:
* This can eventually build up the model to be fine-tuned
* Extend to other specialties:
    * Endocrine
    * Cardiology
    * Surgeons Pre-Op Labs

# Vertex AI "Optimized"
## Lab Results Summarization Tool: Streamlining Patient Communication with AI

This tool automates the process of summarizing and communicating lab results to patients, saving physicians time and improving patient understanding. Developed during a summer internship at Hackensack Meridian Health (HMH), it leverages Google's Gemini-1.5 Pro model for generating clear and actionable summaries from patient lab data.

### Objective & Impact

The tool aims to bridge the gap between complex medical data and patient understanding, resulting in:

* **Enhanced Patient Communication:** Summarized results empower patients to better understand their health status and engage in their care.
* **Physician Time Savings:** Automating the summarization process frees up physicians' time for direct patient interaction.
* **Improved Preventative Care:** The tool includes personalized lifestyle recommendations based on lab results, fostering proactive health management.

**Estimated Time Savings:** Up to 4 hours of physician time per patient can be saved by using this tool.

### Data & Processing

* **Data Source:** Patient data, including age, sex, lab results, and BMI, is extracted from HMH's Electronic Medical Records (EMR) through BigQuery.
* **Data Formatting:** Data is converted into a pipe-delimited format for efficient processing by the Large Language Model (LLM). This format includes:

```
Age:
Sex:
Component|Component_Base|Initial_Value|Initial_Flag|New_Value|New_Flag
```

### Prompt Engineering & Model Selection

The tool utilizes Gemini-1.5 Pro for its superior accuracy and reduced hallucinations compared to other models. It performs two types of analysis:

* **Singular Analysis:** Summarizes the most recent lab results.
* **Comparative Analysis:** Compares the two most recent lab results, highlighting changes and important values.

**Prompt Refinement:** The initial prompt was refined through trial and error to provide:

* **Context:** The model is instructed to act as a primary care physician focused on preventative care.
* **Structured Instructions:** Specific guidelines are provided for document organization, including:
* **Overview of Lab Results:** Highlights significant results and changes.
* **Preventative Care Plan:** Provides personalized recommendations.
* **Follow-Up Instructions:** Outlines next steps and contact information.
* **Style & Tone:** Example outputs are included to ensure consistent formatting and tone.

**Model Selection:** After initial experimentation with MedLM, Gemini-1.5 Pro was chosen due to its improved performance and reliability.

### Learning Methods

* **Zero-Shot Learning:** Initial attempts using zero-shot learning yielded unsatisfactory results.
* **Few-Shot Learning:** Providing three examples of physician notes improved performance but introduced bias towards comparative analysis.
* **Refined Few-Shot Learning:** Tailored examples are supplied based on user request, ensuring appropriate handling of both singular and comparative analysis.

### Example Formatting

* **Input & Output Examples:** Specific examples of input data and expected output are included to demonstrate the tool's functionality.

### Demo & Stakeholder Feedback

* **Demo:** A demo showcasing tool functionality with sample input and output is available (links to be added).
* **Stakeholder Feedback:** Positive feedback from physicians included:
* "80% of the work is done."
* **Must-Haves:** Avoid inflammatory statements and referrals.
* **Nice-to-Haves:** Include clinical ranges, medication and vaccination recommendations.

### Future Enhancements

* **Prompt Optimization:** Utilize DSPy for further prompt engineering improvements.
* **Clinical Range Integration:** Include clinical ranges in the LLM input or EMR data.
* **Test Importance Hierarchy:** Allow stakeholders to prioritize tests for improved summarization.
* **Automated Example Pipeline:** Develop a pipeline to automatically add approved documents to the training examples.
* **Expansion to Other Specialties:** Extend the tool's functionality to other medical disciplines.

This Lab Results Summarization Tool represents a valuable step towards improved patient care and communication. With ongoing development and refinements, it has the potential to significantly impact healthcare delivery.