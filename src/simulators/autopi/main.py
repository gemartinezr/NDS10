"""
This simulator runs on python3.5+. Requires you to have installed python-can for python3
"""

import can
import logging
import struct

#log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

interface = 'socketcan'
channel = 'vcan0'


def handle_message(recv_msg):
    RPM_VALUE = 1000

    logging.info("recv_msg.is_extended_id == {}".format(recv_msg.is_extended_id))
    logging.info("recv_msg.arbitration_id == {:x}".format(recv_msg.arbitration_id))
    logging.info("recv_msg.data == {}".format(recv_msg.data))

    if recv_msg.arbitration_id == 0x7DF:
        data_length = recv_msg.data[0]
        mode        = recv_msg.data[1]
        pid         = recv_msg.data[2:]

        if mode == 0x01:
            logging.info("mode == {}".format(mode))
            logging.info("mode == 0x01: {}".format(mode == 0x01))

            logging.info("pid == {}".format(pid))
            logging.info("pid[0] == {}".format(pid[0]))
            logging.info("pid[0] == 0x0C: {}".format(pid[0] == 0x0C))

            ### RPM ###
            if pid[0] == 0x0C:
                resp_msg = can.Message(arbitration_id=0x7E8, is_extended_id=False, data=[
                    0x04, # data length
                    mode + 0x40,
                    0x0C,
                    *struct.pack(">h", RPM_VALUE * 4), # actual value
                ])

                logging.info("Send msg {}".format(resp_msg))
                bus.send(resp_msg)


bus = can.Bus(channel=channel, interface=interface)
reader = can.BufferedReader()
notifier = can.Notifier(bus=bus, listeners=[reader])

try:
    logging.info("Simulator is listening on {}".format(channel))
    while True:
        msg_recv = reader.get_message()

        if msg_recv:
            logging.info("Received new message: {}".format(msg_recv))
            handle_message(msg_recv)

except KeyboardInterrupt:
    pass

except Exception as e:
    logging.exception("Received exception while listening for new messages")

finally:
    logging.info("Stopping simulator...")
    notifier.stop()
    bus.shutdown()