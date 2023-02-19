# sms-tool
This is a simple tool for sending text messages using the Twilio API. It might be useful if you need to quickly get started with an SMS campaign, but don't have the time/money/experience to develop and deploy a custom solution. You can run the tool from your computer without worrying about cloud infrastructure.

All you need to start is a Twilio account and a CSV file with contact information.

<img width=60% src='https://github.com/probablyfine/sms-tool/raw/main/screenshot.png'>

## Alternatives

There are several alternatives that accomplish something similar. In general, these seem to have some limitations and/or barriers to getting started if you don't have coding experience. Still, you might want to check them out - they could be a better fit for you depending on your needs and existing set-up.

- [Low Code and No Code Tools for Sending SMS](https://www.twilio.com/blog/5-low-codeno-code-tools-to-send-twilio-sms)
- [Deployable CSV-to-SMS App](https://www.twilio.com/blog/serverless-sms-marketing-campaigns-csv)

## Getting Started

### Pre-packaged executable

The easiest way to get started is to download a pre-packaged executable (Windows-only at the moment). It was generated using PyInstaller per the [Kivy docs](https://kivy.org/doc/stable/guide/packaging-windows.html).

[Click here to download the executable.](https://www.dropbox.com/s/s9ncjvh62jeifzs/SMSTool.exe?dl=1)

### Run from source
If you prefer, you can run the tool directly from source. Make sure you have Python 3 installed. **As of this writing, Python 3.11 is not supported by Kivy.** 3.10 should work fine. Then:
* Clone this repository

* Open a terminal and install/update `setuptools` and `virtualenv` (Kivy doesn't seem to work well with `venv`, so use `virtualenv` instead):
`python3 -m pip install --upgrade pip setuptools virtualenv`

* Create a new virtual environment:
`python3 -m virtualenv sms_venv`

* Activate the virtual environment:
	* On macOS/*nix: `source sms_venv/bin/activate`
	* On Windows: `sms_venv\Scripts\activate.bat`

* Navigate to the top-level directory of the repo, and install the required packages:
`python -m pip install -r requirements.txt`

* Finally, run the main script:
`python sms_tool.py`

## Using the tool
Using the tool is very straightforward:

1) To start, you need to grab your Twilio credentials. Log in to your Twilio Console, then copy and paste these three items into the first three fields in the SMS tool (see screenshot at top of page).


<img width=75% src='https://github.com/probablyfine/sms-tool/raw/main/twilio-console.png'>

2) Create a CSV file containing your contacts. 
**IMPORTANT DETAILS:**
    - The tool expects exactly three columns in the CSV file: <u>FirstName</u>, <u>LastName</u>, <u>PhoneNumber</u>. It will blindly assume these columns exist **in this exact order**.
    - The tool will automatically format phone numbers for Twilio (E.164 format).
    - If a number does not appear to be valid, **it will be dropped.**
    - Duplicate numbers **will be dropped.**

3) Drag and drop your CSV file into the tool (anywhere within its window will work).

4) Set the "rate limit" (how fast the messages will be sent). [More details.](https://support.twilio.com/hc/en-us/articles/223183648-Sending-and-Receiving-Limitations-on-Calls-and-SMS-Messages)

5) Type the text of your SMS message into the tool. Be mindful of the number of segments your message will consume. [More details.](https://www.twilio.com/blog/2017/03/what-the-heck-is-a-segment.html)

6) Hit the 'Send' button and watch your messages go out. You can hit 'Pause' any time to stop sending.

That's it! Once all the messages have been sent, just drag and drop a new CSV file into the tool to start over.

## Mild warnings
- This tool does *not* confirm for certain that a message has been delivered. When the status in the tool says "Sent", this only means that Twilio has accepted the *request* to send. Be sure to check the logs in your Twilio Console to confirm things are working as expected.
- Sending tons of messages can get expensive fast - make sure to monitor your usage in the Twilio Console
- Never share your Twilio credentials, since someone else could then send messages and you'll be billed for them.
