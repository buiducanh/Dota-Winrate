import dota2api
import pprint
import os
import datetime
import json
import ast
import time
import threading

data_dir_prefix = "data/"
matches_buffer = []
max_buffer_size = 10000
buffer_flush_counter = 0
max_flush_counter = 5
consume_flag = True
produce_flag = True
buffer_lock = threading.Lock()

api = dota2api.Initialise()

def flush_buffer():
    """NOT THREAD SAFE
    The thread must have ownership of the buffer_lock
    or it is the only thread running
    """
    global matches_buffer
    global buffer_flush_counter
    global consume_flag
    # truncate buffer
    flushed_matches = matches_buffer[:min(max_buffer_size, len(matches_buffer))]
    matches_buffer = matches_buffer[min(max_buffer_size, len(matches_buffer)):]

    buffer_flush_counter += 1
    flush_file = data_dir_prefix + 'valid_matches_%d.json' % (buffer_flush_counter)

    with open(flush_file, 'w') as out:
        json.dump(flushed_matches, out)
        print 'Flushed %d matches' % (len(flushed_matches))
    if buffer_flush_counter >= max_flush_counter:
        # after persisting a certain number of files, flag the consumers to stop
        # NOTE: only guarantee a lower bound of files
        consume_flag = False

def add_matches_to_buffer(matches):
    global matches_buffer
    with buffer_lock:
        print 'Added %d matches to buffer' % (len(matches))
        matches_buffer += matches
        if len(matches_buffer) >= max_buffer_size:
            flush_buffer()


class ThreadFilterAndPersistMatches(threading.Thread):
    def __init__(self, list_of_matches, cv):
        threading.Thread.__init__(self)
        self.list_of_matches = list_of_matches
        self.cv = cv

    def check_players_leaver_status(self, players):
        # Check that all 10 players finished the game
        players_status = map(lambda x: not "leaver_status" in x or x["leaver_status"] == 0, players)
        return reduce(lambda x, y: x & y, players_status)

    def match_criteria(self, match):
        if match["duration"] <= 600: # game must be longer than 10 mins
            return False
        if not self.check_players_leaver_status(match["players"]):
            return False
        if match["lobby_type"] not in [0, 2, 6, 7]:
            # only consider full 5v5 with human players
            return False
        if match["game_mode"] not in [2, 22]:
            # only consider Captain's Mode and Ranked Matchmaking
            return False
        if match["human_players"] != 10:
            # only consider games with 10 players
            return False
        return True


    def run(self):
        while True:
            self.cv.acquire()
            while not self.list_of_matches:
                if not consume_flag or not produce_flag:
                    self.cv.release()
                    return
                self.cv.wait()
            start_id, matches_requested, matches = self.list_of_matches.pop()
            self.cv.release()

            persist_file = data_dir_prefix + 'raw/matches_%d_%d.json' % (start_id, matches_requested)
            with open(persist_file, 'w') as out:
                json.dump(matches, out)

            valid_matches = filter(self.match_criteria, matches)

            add_matches_to_buffer(valid_matches)


class ThreadCollectRawMatches(threading.Thread):
    def __init__(self,
            list_of_matches,
            cv,
            start_id=None,
            matches_requested=25,
            total_results=100,
            rate_limit=1):
        threading.Thread.__init__(self)
        self.list_of_matches = list_of_matches
        self.cv = cv
        self.start_id = start_id
        self.matches_requested = matches_requested
        self.total_results = total_results
        self.count = 0
        self.base_sleep_time = rate_limit

    def run(self):
        sleep_time = self.base_sleep_time
        while self.count < self.total_results and consume_flag:
            persist_file = data_dir_prefix + 'raw/matches_%d_%d.json' % (self.start_id, self.matches_requested)
            self.cv.acquire()
            try:
                if not os.path.isfile(persist_file):
                    resp = api.get_match_history_by_seq_num(
                            matches_requested=self.matches_requested,
                            start_at_match_seq_num=self.start_id,
                            )
                    matches = resp["matches"]
                    sleep_time = self.base_sleep_time
                else:
                    with open(persist_file, "r") as inp:
                        matches = json.load(inp)
                    sleep_time = 0
                self.list_of_matches.append((self.start_id, self.matches_requested, matches))

                if not matches:
                    # stop if the response does not contain any matches
                    print("nothing in resp")
                    self.cv.notify()
                    self.cv.release()
                    break
            except ValueError as err:
                print("Error at request with start_id {0}: {1}".format(self.start_id, err))
            finally:
                self.count += self.matches_requested
                if self.count % 2000 == 0:
                    print 'Collected %d matches' % (self.count)
                self.start_id += self.matches_requested

                self.cv.notify()
                self.cv.release()

                time.sleep(sleep_time) # rate limit to 1 req / sleep_time (s)

        global produce_flag
        produce_flag = False
        self.cv.acquire()
        self.cv.notifyAll()
        self.cv.release()
        print('Collected %d matches' % (self.count))


list_of_matches = []
cv = threading.Condition()
start_id = 2718091806
matches_collect_size = 100000
matches_requested = 100
rate_limit = 7

thread_collect_matches = ThreadCollectRawMatches(
        list_of_matches,
        cv,
        start_id=start_id,
        matches_requested=matches_requested,
        total_results=matches_collect_size,
        rate_limit= 7
        )

n_thread_process_matches = 2
l_thread_process_matches = [ThreadFilterAndPersistMatches(
        list_of_matches,
        cv
        ) for i in range(n_thread_process_matches)]

thread_collect_matches.start()
for thread in l_thread_process_matches:
    thread.start()

thread_collect_matches.join()
for thread in l_thread_process_matches:
    thread.join()

# flush if there are still games in buffer
if matches_buffer:
    flush_buffer()


"""    for match in matches["matches"]:
        timestamp = match["start_time"]
        converted = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        match["start_time"] = converted

    out = open('matches_%d.json' % (start_id), "w")

    json.dump(matches, out)
    pprint.pprint(matches)
else:
    with open('matches_%d.json' % (start_id), "r") as inp:
        matches = json.load(inp)
        pprint.pprint(matches)"""

"""if not os.path.isfile("match_history.json"):
    while True:
        matches = api.get_match_history(
                game_mode=1,
                skill=3,
                min_players=10,
                matches_requested=10
                #start_at_match_id=start_id
                )
        if matches["num_results"] == 0:
            start_id += 500
            pprint.pprint(matches)
            print('none at %d' % (start_id))
            time.sleep(1)
        else:
            for match in matches["matches"]:
                timestamp = match["start_time"]
                converted = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                match["start_time"] = converted

            out = open("match_history.json", "w")

            json.dump(matches, out)
            pprint.pprint(matches)
            break
else:
    with open("match_history.json", "r") as inp:
        matches = json.load(inp)
        pprint.pprint(matches)
"""
