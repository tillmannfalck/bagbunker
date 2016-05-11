#!/usr/bin/env python
import argparse
import os
import rosbag
import pyproj
import numpy as np
import yaml
import rospy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
import json

class Status:
    # Results for Sanitychecks
    OK = 0 # status OK
    TOHIGH = 1 # status warning
    TOLOW = 2 # status error
    NONEXIST = 3 # status error
    UNSYNCED = 4 # status error
    ERROR = 5 # status error

    # Map testresults to ROS status conditions
    ROSSTATUS = [DiagnosticStatus.OK, DiagnosticStatus.WARN, DiagnosticStatus.ERROR, DiagnosticStatus.ERROR, DiagnosticStatus.ERROR, DiagnosticStatus.ERROR]


class SanityCheck(object):
    def __init__(self):
        # Create main data dict for ROS info
        self.data = dict()


    # Get Summary Information and store in member variable
    def load_bagfile(self, input_bag):
        self.data = yaml.load(rosbag.Bag(input_bag, 'r')._get_yaml_info())
        return self.data


    # Create associate array with topics and coresponding frequencies
    def topics_frequencies(self):
        topics = dict()
        duration = self.get_duration();
        for topic in self.data['topics']:
            if topic['messages'] > 1:
                topics[topic['topic']] = np.floor(topic['messages']/duration*10000)/10000.0
            else:
                topics[topic['topic']] = 0

        return topics


    # Create associate array with topics and coresponding message amount
    def topics_messages(self):
        topics = dict()
        for topic in self.data['topics']:
            topics[topic['topic']] = topic['messages']

        return topics


    # Return first message of given topic
    def first_message(self, input_bag, search_topic, timeframe):
        with rosbag.Bag(input_bag, 'r') as input_file:
            for topic, msg, t in input_file.read_messages(topics=search_topic.keys(), end_time=rospy.Time.from_sec(self.data['start']+timeframe)):
                message_content = [msg.header.stamp.to_sec()]
                for value in search_topic[topic]:
                    message_content.append(getattr(msg, value))

                # brake after first message is found
                break

        return message_content


    # Return last message of given topic
    def last_message(self, input_bag, search_topic, timeframe):
        with rosbag.Bag(input_bag, 'r') as input_file:
            for [topic, msg, t] in input_file.read_messages(topics=search_topic.keys(), start_time=rospy.Time.from_sec(self.data['end']-timeframe)):
                message_content = [msg.header.stamp.to_sec()]
                for value in search_topic[topic]:
                    message_content.append(getattr(msg, value))

        return message_content



    # Get diagnostic messages with given name
    # CPU load: module_name + "/cpu_monitor CPU Usage"
    def diagnostic_messages(self, input_bag, message_name):
        # return list
        message_list = list()
        # Read bagfile
        with rosbag.Bag(input_bag, 'r') as input_file:
            # go through selected messages (/diagnostic topic)
            for [topic, msg, t] in input_file.read_messages(topics='/diagnostics'):
                # go through the list of stati in msg
                for sub_status in msg.status:
                    # continue if a status fits the given messsage_name
                    if sub_status.name == message_name:
                        # go though key/value pairs to create a dict
                        status_info = dict()
                        for key_value_pair in sub_status.values:
                            status_info[key_value_pair.key] = key_value_pair.value
                        message_list.append(status_info)

        return message_list



    # Time difference between two messages
    def time_difference(self, first_message, second_message):
        return (second_message[0] - first_message[0])



    # Calculate track length using first and last GPS message
    def gps_track_length(self, input_bag):
        # Projection for GPS coordinates
        proj = pyproj.Proj(proj='utm', zone=32, ellps='WGS84')

        # Get first and last message from topics
        topic = dict()
        topic['/gps/fix'] = ['latitude', 'longitude', 'altitude']
        first_message = self.first_message(input_bag, topic, 10)
        last_message = self.last_message(input_bag, topic, 5)

        # Convert coordinates
        [e1, n1] = proj(first_message[2], first_message[1])
        [e2, n2] = proj(last_message[2], last_message[1])

        # Return distance between start and end point
        de = e2-e1
        dn = n2-n1
        return np.sqrt(de*de + dn*dn)



    # Get GPS erros from diagnostics aggregator '/sanity_check/diagnostics_agg'
    def gps_errors(self, input_bag):
        # return list
        message_list = list()
        # Read bagfile
        with rosbag.Bag(input_bag, 'r') as input_file:
            # go through selected messages (/sanity_check/diagnostics_agg)
            for [topic, msg, t] in input_file.read_messages(topics='/sanity_check/diagnostics_agg'):
                # Check only the first status (aggegated one)
                sub_status = msg.status[0]
                # continue if a status has error level (2) or above
                if sub_status.level >= 2:
                    # collect all errors in list
                    message_list.append(sub_status.values[0].value)

        return message_list



    # Get size of bag-file (using ROS header info)
    def get_filesize(self):
        if self.data.has_key('uncompressed'):
            return self.data['uncompressed']
        else:
            return self.data['size']



    # Get duration of bag-file (using ROS header info)
    def get_duration(self):
        return self.data['duration']


    # Load config file
    def load_configfile(self, filename, module_name):
        with open(filename, 'r') as stream:
            yaml_file = yaml.load(stream)
            topics_new = { x.replace('camX', module_name): yaml_file['topics'][x] for x in yaml_file['topics'].keys() }
            yaml_file['topics'] = topics_new
            return yaml_file


    # Analyse Bag-file
    # Checks:
    # - All Topics from config file list are recorded with correct frequency
    #     > returns list with topics and frequency in Hz
    # - GPS track between start and end min/max XX m
    #     > returns distance in meter
    # - Record Time min/max XX s
    #     > returns time in seconds
    # - Bag-file min/max XX GB
    #     > returns file size in GB
    # - Check diagnostic '/sanity_check/diagnostics_agg' for errors
    #     > return number of errors
    # - TODO: Bag-file is older than XX s
    def analyse_bag_file(self, input_bag, input_yaml, module_name):
        # Load bag-file Info
        self.load_bagfile(input_bag)

        # Load config data from yaml file
        config_data = self.load_configfile(input_yaml, module_name)

        # Reindex topics with topic-names for easier access
        frequencies = self.topics_frequencies()
        messages = self.topics_messages()

        # Create dict for results
        results = list()

        # Go through topic list from config file and check frequency of messages
        for topic in sorted(config_data['topics']):
            if frequencies.has_key(topic):
                frequency = frequencies[topic]
                if config_data['topics'][topic].has_key('min') and frequency < config_data['topics'][topic]['min']:
                    stat = Status.TOLOW
                elif config_data['topics'][topic].has_key('max') and frequency > config_data['topics'][topic]['max']:
                    stat = Status.TOHIGH
                else:
                    stat = Status.OK
            else:
                stat = Status.NONEXIST
                frequency = -1

            # Add to results dict
            results.append([topic, frequency, stat])

        # Get duration of bag-file
        duration = float(np.round(self.get_duration(), 1))
        if config_data['duration'].has_key('min') and duration < config_data['duration']['min']:
            stat = Status.TOLOW
        elif config_data['duration'].has_key('max') and duration > config_data['duration']['max']:
            stat = Status.TOHIGH
        else:
            stat = Status.OK
        results.append(["Duration", duration, stat])

        # Get uncompressed file size of bag-file
        filesize = float(np.round(self.get_filesize()/1073741824.0, 3))
        if config_data['filesize'].has_key('min') and filesize < config_data['filesize']['min']:
            stat = Status.TOLOW
        elif config_data['filesize'].has_key('max') and filesize > config_data['filesize']['max']:
            stat = Status.TOHIGH
        else:
            stat = Status.OK
        results.append(["Filesize", filesize, stat])

        # Get Tracklength from GPS messages (if requested)
        if config_data.has_key('tracklength'):
            if frequencies.has_key('/gps/fix'):
                tracklength = float(np.round(self.gps_track_length(input_bag), 2))
                if config_data['tracklength'].has_key('min') and tracklength < config_data['tracklength']['min']:
                    stat = Status.TOLOW
                elif config_data['tracklength'].has_key('max') and tracklength > config_data['tracklength']['max']:
                    stat = Status.TOHIGH
                else:
                    stat = Status.OK
            else:
                stat = Status.NONEXIST
                tracklength = -1
            results.append(["Tracklength", tracklength, stat])

        # Check for synced messages (only if keyword is used in config.yaml)
        if config_data.has_key('synced'):
            # Go through synced groups
            for group in config_data['synced']:
                # Get min and max of all messages in synced group
                message_min = -1
                message_max = 0
                for topic in config_data['synced'][group]:
                    topic_fix = topic.replace('camX', module_name)
                    # if topic has no message, set message number to 0
                    if not messages.has_key(topic_fix):
                        messages[topic_fix] = 0
                    if messages[topic_fix] < message_min or -1 == message_min:
                        message_min = messages[topic_fix]
                    if messages[topic_fix] > message_max:
                        message_max = messages[topic_fix]
                # Add group synced result to global results
                diff = message_max - message_min
                if diff > 10:
                    stat = Status.UNSYNCED
                else:
                    stat = Status.OK
                results.append(["Synced " + group, diff, stat])

        # Check for GPS errors
        gps_diag = self.gps_errors(input_bag)
        if len(gps_diag) > 0:
            stat = Status.ERROR
        else:
            stat = Status.OK
        results.append(["GPS Errors", len(gps_diag), stat])

        # Return results
        return results


    # Send Diagnostic ROS message
    def send_diagnostic(self, pub, input_bag, results):

        diag_status = DiagnosticStatus()
        diag_status.message = "SanityCheck file: " + input_bag
        diag_status.name = "SanityChecker Result"

        for check in results:
            out_str = check[0]
            rosstatus = Status.ROSSTATUS[check[2]]
            if Status.NONEXIST == check[2]:
                out_str = out_str + ": NOT EXISTING"
            elif Status.TOLOW == check[2]:
                out_str = out_str + ": value to low"
            elif Status.TOHIGH == check[2]:
                out_str = out_str + ": value to high"
            elif Status.OK == check[2]:
                out_str = out_str + ": OK"
            elif Status.UNSYNCED == check[2]:
                out_str = out_str + ": UNSYNCED"
            elif Status.ERROR == check[2]:
                out_str = out_str + ": ERROR"
            else:
                out_str = out_str + ": Status " + str(check[2]) + " unknown"
                rosstatus = DiagnosticStatus.ERROR

            if (DiagnosticStatus.ERROR == rosstatus or
                (DiagnosticStatus.OK == diag_status.level and DiagnosticStatus.WARN == rosstatus)):
                diag_status.level = rosstatus

            diag_status.values.append(KeyValue(key=out_str, value=str(check[1])))

        # Create ROS message
        msg = DiagnosticArray()
        msg.header.stamp = rospy.get_rostime()
        msg.status.append(diag_status)

        # Publish ROS message
        pub.publish(msg)


    # Output results as json syntax
    def json_output(self, results):
        success = True
        for check in results:
            if check[2] != Status.OK and check[2] != Status.TOHIGH:
                success = False
                break

        print(json.dumps({'success': success, 'details': results}))


    # Colored prints for terminal output
    def printY(self, str):
        print("\033[93m" + str + "\033[0m")

    def printR(self, str):
        print("\033[91m" + str + "\033[0m")

    def printG(self, str):
        print("\033[92m" + str + "\033[0m")


if __name__ == '__main__':
    # parsing input arguments
    parser = argparse.ArgumentParser(description='Performs Sanity Check on given bag file')
    parser.add_argument('input_bag', help='Rosbag to extract from')
    parser.add_argument('--input_yaml', help='Yaml with topic list and thresholds')
    parser.add_argument('--module_name', help='Module name (camA, camB, camC, main)')
    parser.add_argument('--ros', action='store_true', help='Results are published as ros /diagnostics message instead of the terminal')
    parser.add_argument('--json', action='store_true', help='Results are printed in json format instead of human readable')
    args = parser.parse_args()

    # If ros output is used
    if args.ros:
        # Initialize ROS node
        try:
            rospy.init_node('SanityChecker')
        except rospy.exceptions.ROSInitException:
            print('SanityChecker is unable to initialize node. ROS master may not be running.')
            sys.exit(2)

        # Create publisher for diagnostic ROS messages
        pub = rospy.Publisher('/diagnostics', DiagnosticArray, queue_size=1)


    # Create SanityCheck object
    sc = SanityCheck()

    # Use default settings if not provided, otherwise try to find correct settings from bag-name
    input_bag = args.input_bag
    input_yaml = args.input_yaml
    module_name = args.module_name

    input_bag_split = input_bag.split('__')

    if not module_name:
        module_name = input_bag_split[-1][0:4]

    if not input_yaml:
        input_yaml = os.path.dirname(os.path.realpath(__file__)) + "/"
        input_yaml +=  "sanity_check_"
        if module_name == "main":
            input_yaml += "main"
        else:
            input_yaml += input_bag_split[3]
        input_yaml += ".yaml"


    # Do bag file analysis
    results = sc.analyse_bag_file(input_bag, input_yaml, module_name)

    # If ros output is used
    if args.ros:
        # Send ROS message
        if not rospy.is_shutdown():
            sc.send_diagnostic(pub, args.input_bag, results)

    # If json output is used
    if args.json:
        sc.json_output(results)

    # If neither json nor ros output is used, use terminal in human readable
    if not args.ros and not args.json:
        print "use input_yaml: " + input_yaml
        print "use module_name: " + module_name
        for result in results:
            if result[2] == Status.OK:
                sc.printG(result[0] + ": " + str(result[1]))
            elif result[2] == Status.TOHIGH:
                sc.printY(result[0] + ": " + str(result[1]))
            elif result[2] == Status.TOLOW:
                sc.printR(result[0] + ": " + str(result[1]))
            elif result[2] == Status.NONEXIST:
                sc.printR(result[0] + ": MISSING")
            elif result[2] == Status.UNSYNCED:
                sc.printR(result[0] + ": " + str(result[1]))
            elif result[2] == Status.ERROR:
                sc.printR(result[0] + ": " + str(result[1]))
            else:
                sc.printR(result[0] + ": UNKNOWN STATUS " + str(result[2]))
