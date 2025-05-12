import can
import logging

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

INTERFACE = 'socketcan'
CHANNEL = 'vcan0'

CUSTOM_REPLIES = {
    "7DF#02010C0000000000": [ "7E8#04410C0BB8AAAAAA" ],
    "7DF#0201000000000000": [ "7EA#06410080000001AA", "7E8#064100D83B8013AA" ],
    "7DF#0201200000000000": [ "7EA#06412080000000AA", "7E8#064120A019A001AA" ],
    "7DF#0201400000000000": [ "7E8#064140CCDC805DAA" ],
    "7DF#0206000000000000": [ "7E8#06460000000001AA" ],
    "7DF#0206200000000000": [ "7E8#06462000008000AA" ],

    # BMW i3 HV_BAT_SOC
    "6F1#070322DDBC000000": [ "607#F1037F2278", "607#F1100962DDBC019A" ], # obd.query mode=x22 pid=xDDBC header=x6F1 can_extended_address='07' can_flow_control_clear=True can_flow_control_filter=607,FFF can_flow_control_id_pair=6F1,607F1 protocol=6 baudrate=500000 frames=1 force=true verify=false formula="bytes_to_hex(messages[0].data)" HV_BAT_SOC
}


def handle_message(msg, bus):
    header_in_hex = "{:x}".format(msg.arbitration_id).upper()
    data_in_hex = "".join(["{:02x}".format(b) for b in msg.data]).upper()

    can_frame = "{}#{}".format(header_in_hex, data_in_hex)
    log.info("Received: {}".format(can_frame))

    responses = CUSTOM_REPLIES.get(can_frame, None)

    if responses == None:
        log.error("Couldn't find any responses for this message, noop")
        return

    log.info("Found responses for this message: {}".format(responses))
    for res in responses:
        header_str, payload_str = res.split("#")

        header = int(header_str, 16)

        payload_chunks = [payload_str[i] + payload_str[i+1] for i in range(0, len(payload_str), 2)]
        payload_chunks = [int(chunk, 16) for chunk in payload_chunks]

        log.info("Header: {}".format(header))
        log.info("Payload chunks: {}".format(payload_chunks))

        res_msg = can.Message(
            arbitration_id=header,
            is_extended_id=header > 0x7FF,
            data=payload_chunks,
        )

        log.info("Prepared message: {}".format(res_msg))
        bus.send(res_msg)


def main():
    # Setup bus
    bus = can.Bus(channel=CHANNEL, interface=INTERFACE)
    reader = can.BufferedReader()
    notifier = can.Notifier(bus=bus, listeners=[reader])

    try:
        logging.info("Simulator is listening on {}".format(CHANNEL))
        while True:
            msg_recv = reader.get_message()

            if msg_recv:
                logging.info("Received new message: {}".format(msg_recv))
                handle_message(msg_recv, bus)

    except KeyboardInterrupt:
        pass

    except Exception as e:
        logging.exception("Received exception while listening for new messages")

    finally:
        logging.info("Stopping simulator...")
        notifier.stop()
        bus.shutdown()

if __name__ == "__main__":
    main()
