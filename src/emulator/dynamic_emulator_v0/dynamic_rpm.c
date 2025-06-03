#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>
#include <time.h>

#define PHASE_LEN 30
#define CYCLE_LEN 90

int rpm_lookup_low[PHASE_LEN];
int rpm_lookup_medium[PHASE_LEN];
int rpm_lookup_high[PHASE_LEN];

void init_rpm_lookup() {
    for (int i = 0; i < PHASE_LEN; i++) {
        rpm_lookup_low[i] = 4000 + i * 70;
        rpm_lookup_medium[i] = 6000 + i * 200;
        rpm_lookup_high[i] = 12000 + i * 270;
    }
}

int main() {
    int s;
    struct sockaddr_can addr;
    struct ifreq ifr;
    struct can_frame frame;
    time_t start_time = time(NULL);

    init_rpm_lookup();

    if ((s = socket(PF_CAN, SOCK_RAW, CAN_RAW)) < 0) {
        perror("Socket");
        return 1;
    }

    strcpy(ifr.ifr_name, "can0");
    ioctl(s, SIOCGIFINDEX, &ifr);

    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    if (bind(s, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("Bind");
        return 1;
    }

    while (1) {
        if (read(s, &frame, sizeof(struct can_frame)) < 0) continue;

        if (frame.can_id == 0x7DF && frame.can_dlc >= 3 &&
            frame.data[1] == 0x01 && frame.data[2] == 0x0C) {

            // Determine phase + index
            time_t elapsed = time(NULL) - start_time;
            int second = elapsed % CYCLE_LEN;
            int rpm = (second < 30)
                        ? rpm_lookup_low[second]
                        : (second < 60)
                            ? rpm_lookup_medium[second - 30]
                            : rpm_lookup_high[second - 60];

            struct can_frame reply;
            reply.can_id = 0x7E8;
            reply.can_dlc = 8;
            reply.data[0] = 4;
            reply.data[1] = 0x41;
            reply.data[2] = 0x0C;
            reply.data[3] = (rpm >> 8) & 0xFF;
            reply.data[4] = rpm & 0xFF;
            reply.data[5] = reply.data[6] = reply.data[7] = 0;

            write(s, &reply, sizeof(struct can_frame));
        }
    }

    close(s);
    return 0;
}
