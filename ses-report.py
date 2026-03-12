#!/usr/bin/env python3

import argparse
import datetime
import json
import pathlib
from collections import defaultdict
import logging
import email.message
import smtplib
import socket
import os
from dynaconf import Dynaconf

# Load configuration
settings = Dynaconf(
    settings_files=['config.yaml'],
    root_path=os.path.dirname(os.path.realpath(__file__))
)

def command_line_arguments():
    parser = argparse.ArgumentParser(description='Generate SES report', allow_abbrev=False)
    parser.add_argument('--email', action='store_true', default=False, help="Send report by email.")
    parser.add_argument('--quiet', action='store_true', default=False, help="Do not print anything to stdout.")
#    parser.add_argument("--config-file", type=pathvalidate.argparse.validate_filepath_arg, default=f"{os.path.dirname(os.path.realpath(__file__)) }/config.yaml")
    parser.add_argument('--debug', action='store_true', default=False, help="Print debug messaages to terminal" )
    parser.add_argument('--store-data', action='store_true', default=False, help="Store report data to JSON Lines file.")
    return parser.parse_args()

# ----------------------------------------------------------------------------------------------------------------

def send_email(from_addr, to_addr, subject, body):
    logging.debug('send_email()')
    msg = email.message.EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    #print(body)
    msg.set_content(body)
    smtpObj = smtplib.SMTP(settings.email.smtp_server)
    try:
        smtpObj.send_message(msg)
    except Exception as e:
        logging.error(f'Error sending email: {e}')
        print(e)
    smtpObj.quit()

# ----------------------------------------------------------------------------------------------------------------

def get_data(mypath):
    myfiles = [item for item in mypath.iterdir() if item.is_file()]

    message_type_count = defaultdict(int)
    sent_from_count = defaultdict(int)

    for f in myfiles:
        with open(f, 'r') as read_file:
            data = json.load(read_file)
            message = json.loads(data['Message'])
            message_type_count[message['eventType']] += 1
            if message['eventType'] == 'Send':
                sent_from_count[message['mail']['tags']['ses:caller-identity'][0]] += 1

    return (message_type_count, sent_from_count)

# ----------------------------------------------------------------------------------------------------------------

def make_report(message_type_count, sent_from_count):
    report = ''
    for key in message_type_count:
        report += f'{key}: {message_type_count[key]}\n'

    report += '\n'

    for key in sorted(sent_from_count):
        report += f'{key}: {sent_from_count[key]}\n'
    
    report += "\n\n"
    report += f"{socket.gethostname()}\n"
    report += f"{os.path.dirname(os.path.realpath(__file__))}"


    return report

# ----------------------------------------------------------------------------------------------------------------

def store_data(report_date, data_path, message_type_count, sent_from_count, hostname, script_path):
    """Store daily report data as JSON Lines, one file per year in reports/ subdirectory.
    If an entry for the date already exists, it will be replaced."""
    logging.debug('store_data()')

    # Create reports directory if it doesn't exist
    reports_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) / 'reports'
    reports_dir.mkdir(exist_ok=True)

    # Determine year file
    year_file = reports_dir / f'{report_date.year}.jsonl'

    # Prepare new data structure
    new_data = {
        'date': report_date.isoformat(),
        'path': str(data_path),
        'events': dict(message_type_count),
        'senders': dict(sent_from_count),
        'hostname': hostname,
        'script_path': script_path
    }

    # Read existing entries (if file exists) and filter out any matching date
    existing_entries = []
    if year_file.exists():
        with open(year_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                if entry['date'] != report_date.isoformat():
                    existing_entries.append(entry)

    # Write all entries back (existing + new)
    with open(year_file, 'w') as f:
        for entry in existing_entries:
            f.write(json.dumps(entry) + '\n')
        f.write(json.dumps(new_data) + '\n')

    logging.info(f'Stored data to {year_file}')

# ----------------------------------------------------------------------------------------------------------------
def main():
    logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
    args = command_line_arguments()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        pass
    else:
        logging.getLogger().setLevel(logging.INFO)
    mydate = datetime.date.today() - datetime.timedelta(days=settings.report.days_back)
    mypath = pathlib.Path(f'{settings.paths.sns_messages_dir}/{mydate.year}/{mydate.month:02}-{mydate.day:02}')
    (message_type_count, sent_from_count) = get_data(mypath)
    report = f'{mypath}\n\n{make_report(message_type_count, sent_from_count)}'
 
    if not args.quiet:
        print(report, end='')

    if args.email:
        send_email(settings.email['from'], settings.email.to, settings.email.subject, report)

    if args.store_data:
        store_data(mydate, mypath, message_type_count, sent_from_count,
                   socket.gethostname(), os.path.dirname(os.path.realpath(__file__)))
# ----------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
