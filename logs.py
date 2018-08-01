from pythonjsonlogger import jsonlogger
import datetime


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        # fix timestamp to correct ISO
        # this doesn't use record.created, so it is slightly off
        now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        log_record['timestamp'] = now
        if not 'component' in log_record:
            log_record['component'] = 'vnfipsec'
