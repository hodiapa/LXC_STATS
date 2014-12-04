/* getRawPower9.12.c 
 * For use with Carrier Board 10016424 Rev E8 (= Rev A)
 * University of North Carolina,  Q199877, WO000466
 * Niveus 5200 workstations with Tesla K20 and Solarflare SFN5152F, 
 * both on risers.
 *
 * Change history: 
 * getRawPower9.11.c  5/9/2014    Created
 */

#include <stdint.h>
#include <unistd.h>
#include <errno.h>
#include <error.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>	// SPI_MODE_0,

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define SPI_BITS         (8)
#define SPI_DELAY        (0)
#define SPI_SPEED        (1000000)
#define MEASURE_AMPS     1
#define MEASURE_VOLTS    0
#define MAX_PORTNUM      15

// Offset = .1*Vdd
// Gain = 185mV/1000mA @ 5V Vdd
// Raw unit = Vdd/1024
// Amps = ((raw * Vdd/1024) - Offset) / Gain
// mAmps = ((raw * 5000/1024) - 5000/10) / (185/1000)
// mAmps = ((raw*10) - 1024) * 5000/(1024*10) * (1000/185)
// mAmps = (raw*10 - 1024)*500000/(1024*185)

#define SAMPLE2MAMPS(x)    (((x)*10-1024)*(500000.0/(180*1024)))

// Vref = 4.096V
// Raw unit = 4.096/65536 = 1/16 mV
// Voltage divider R1 over R2
// mVolts = raw * ((R1+R2)/R2) /16
#define SAMPLE_TO_12VOLTS(Vsamp)    ((Vsamp)*535/(133*16))  // 40.2k/13.3k

#define SAMPLE_TO_5VOLTS(Vsamp)     ((Vsamp)*414/(249*16))  // 16.5k/24.9k

#define SAMPLE_TO_3_3VOLTS(Vsamp)   ((Vsamp)*121/(110*16))  // 11k/110k

static uint16_t spiTransfer(int fd, int port);
static uint16_t spiVTransfer(int fd, int port);
static uint16_t ainTransfer(int fd, int port);
static void printUsage(const char *prog);
static void getArgs(int argc, char *argv[]);
void getReadings(int portNumber);		// port numbers are cardinal 
void openSPI( int dev );
void openAIN( int dev );

/* 
 *  There are 3 spi chip selects available: 
 *  CS0 on spiBus 1 (spidev1.0)  (shows as SPI0_CS0 on the schematic)
 *  CS0 on spiBus 2 (spidev2.0)  (shows as SPI1_CS0 on the schematic)
 *  CS1 on spiBus 2 (spidev2.1)  (shows as SPI1_CS1 on the schematic)
 */
struct {
   int  fd ;             // FD assigned to an opened FD
   const char *  file ;  // Name of file to be opened
   uint16_t  (*xfer)(int fd, int port) ;  // Transfer function to read
   void  (*open)( int dev );  // Open function
} devList[] = {
        { -1, "/dev/spidev1.0", spiTransfer, openSPI },
        { -1, "/dev/spidev2.0", spiVTransfer, openSPI },
        { -1, "/dev/spidev2.1", spiTransfer, openSPI },
        { -1, "/sys/devices/platform/omap/tsc/ain1", ainTransfer, openAIN },
        { -1, "/sys/devices/platform/omap/tsc/ain2", ainTransfer, openAIN },
        { -1, "/sys/devices/platform/omap/tsc/ain3", ainTransfer, openAIN },
        { -1, "/sys/devices/platform/omap/tsc/ain4", ainTransfer, openAIN },
        { -1, "/sys/devices/platform/omap/tsc/ain5", ainTransfer, openAIN },
        { -1, "/sys/devices/platform/omap/tsc/ain6", ainTransfer, openAIN },
        { -1, "/sys/devices/platform/omap/tsc/ain7", ainTransfer, openAIN }
    }; ;

typedef struct reading {
    uint16_t    Asamp;          // Raw sample
    uint16_t    Vsamp;          // Raw sample
    int32_t     miliamps;       // Calculated value
    int32_t     milivolts;      // Calculated value
    int32_t     miliwatts;      // Calculated value
} reading_t;

reading_t sample;


typedef struct portConfig {
    int         ampsADC_chNum;
    int         voltsADC_chNum;
    int         AmpSpiDevNum;
    int         VoltSpiDevNum;
} portConfig_t;

/* 
 * Port numbers in the comments below are the index into this table.
 * Amps chNum is MPC3008 channel measuring this port's amp or volt signal.
 */
static portConfig_t  portConfig[] = {
/*                 Amps        Volts
     Amps  Volts   SPI device  SPI device
     chNum chNum   Number      Number
*/
    {7,    7,      2,          2},       // port dummy 
    {0,    0,      0,          1},       // port 1 
    {1,    1,      0,          1},       // port 2
    {2,    2,      0,          1},       // port 3
    {3,    3,      0,          1},       // port 4
    {4,    4,      0,          1},       // port 5
    {5,    5,      0,          1},       // port 6
    {6,    6,      0,          1},       // port 7
    {7,    7,      0,          1},       // port 8
    {0,    1,      2,          3},       // port 9   ain<VchNum>
    {1,    2,      2,          4},       // port 10
    {2,    3,      2,          5},       // port 11
    {3,    4,      2,          6},       // port 12
    {4,    5,      2,          7},       // port 13
    {5,    6,      2,          8},       // port 14
    {6,    7,      2,          9},       // port 15
};  


/***********************************************************/
static uint16_t spiTransfer(int fd, int port)
{
    int         result, i;
    uint16_t    retVal; 
    uint8_t     tx[] = { 0x01, 0x00, 0x00, };
    uint8_t     rx[] = { 0,    0,    0,    };
    int         txLen = 3;

    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = (unsigned long)rx,
        .len = txLen, 
        .delay_usecs = SPI_DELAY,
        .speed_hz = SPI_SPEED,
        .bits_per_word = SPI_BITS,
    };

    tx[1] = 0x80 | ((port & 0x7) << 4) ;

    errno = 0 ;
    result = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);

    if (result < 1) {
        error( 0, errno, "In spiTransfer, ioctl() returned 0x%x\n", result);
        retVal = 0 ;
    } else {
        // mask sample bits received from MPC3008
        retVal = (((rx[1] & 3) << 8) | rx[2]);
    }
    return(retVal);
}   // end spiTransfer()


/***********************************************************/
static uint16_t spiVTransfer(int fd, int port)
{
    uint16_t retVal ;

    // Normal read
    retVal = spiTransfer( fd, port );

    // Scale to 16bit fraction of 4.096 volts
    return ( retVal * 64 );
}

/***********************************************************/
static uint16_t ainTransfer(int fd, int port)
{
    int  i ;
    char  buf[16] ;
    char  actual ;
    int  val, sum, min, max ;
    uint16_t  retVal; 

    lseek( fd, 0, SEEK_SET );
    actual = read( fd, buf, sizeof(buf) -1 );
    buf[actual] = '\0' ;
    min = val = atoi( buf );
    max = 0 ;
    
    sum = 0 ; 
    for( i = 17 ; i ; --i ) {
        lseek( fd, 0, SEEK_SET );
        actual = read( fd, buf, sizeof(buf) -1 );
        if( actual > 0 ) {
            buf[actual] = '\0' ;
            val = atoi( buf );
        };
        if( val < min ) {
            sum += min ;
            min = val ;
        } else if( val > max ) {
            sum += max ;
            max = val ;
        } else {
            sum += val ;
        };
    };

    // raw * 1800mV/4096 = mV
    // mV * 218/118 = mV reverse 11.8k pulldown
    // mV * 16 = 16bit fraction of 4.096V
    //  *16 = 16 summed samples
    retVal = sum *((1800.0/4096)*(218.0/118));

    // With 10k pulldown, it would be
    // retVal = sum *((1800.0/4096)*(20.0/10)*2)
    // retVal = sum *(1800.0/1024)

    return retVal ;
}


/***********************************************************/
static void printUsage(const char *prog)
{
	puts("");
	printf("Usage: %s [po po ... ]\n", prog);
	puts("    where po == port number to be queried\n"
	     "    po has range [1..7]\n"
	     "    A port is the connector cabled to a sensor board.");
	printf("    Example: %s 1 2 3 4 5 6 7\n\n", prog);
	exit(1);
}


/***********************************************************/
void getReadings(int portNumber) 
{
    int  dev, fd, port ;

    // Get Amps device for this port
    dev = portConfig[portNumber].AmpSpiDevNum ;
    port = portConfig[portNumber].ampsADC_chNum ;

    // Has it been opened?
    if( devList[dev].fd < 0 ) {
        // No, Open it
        (devList[dev].open)( dev );
    };
    fd = devList[dev].fd ;

    // get amps sample
    sample.Asamp = (devList[dev].xfer)( fd, port );

    // Get Volts device for this port
    dev = portConfig[portNumber].VoltSpiDevNum ;
    port = portConfig[portNumber].voltsADC_chNum ;

    // Has it been opened?
    if( devList[dev].fd < 0 ) {
        (devList[dev].open)( dev );
    };
    fd = devList[dev].fd ;

    // get volts sample (16bit fraction of 4.096 volts)
    sample.Vsamp = (devList[dev].xfer)( fd, port );

}   // end get_readings()


/***********************************************************/
void openSPI( int dev )
{
    int  fd ;
    int  retVal, setting ;

    // Make sure it's not already open?
    if( devList[dev].fd >= 0 ) {
        return ;
    };

    // Open SPI device
    fd = open(devList[dev].file, O_RDWR);
    if (fd < 0) {
        error( 1, errno, "Error opening %s read/write", devList[dev].file );
    };

    // INITIALIZE SPI:
    setting = SPI_MODE_0 ;
    retVal = ioctl(fd, SPI_IOC_WR_MODE, &setting);
    if (retVal == -1) {
        error( 1, errno, "Can't set %s mode to 0", devList[dev].file );
    };

    setting = SPI_BITS ;
    retVal = ioctl( fd, SPI_IOC_WR_BITS_PER_WORD, &setting );
    if (retVal == -1) {
        error( 1, errno, "Can't set %s bits per word to %d", devList[dev].file, SPI_BITS );
    };

    setting = SPI_SPEED;
    retVal = ioctl( fd, SPI_IOC_WR_MAX_SPEED_HZ, &setting );
    if (retVal == -1) {
        error( 1, errno, "Can't set %s max speed to %d", devList[dev].file, SPI_SPEED );
    };

    // Throw away one conversion to reset charge buckets
    // See datasheet errata for MCP3008
    spiTransfer(fd, 0);

    // Completed, save it
    devList[dev].fd = fd ;

}

/***********************************************************/
void openAIN( int dev )
{
    int  fd ;
    int  retVal, setting ;

    // Make sure it's not already open?
    if( devList[dev].fd >= 0 ) {
        return ;
    };

    // Open AIN device
    fd = open(devList[dev].file, O_RDONLY);
    if (fd < 0) {
        error( 1, errno, "Error opening %s read only", devList[dev].file );
    };

    // Completed, save it
    devList[dev].fd = fd ;
}

/***********************************************************/
void calcValues(int portNumber)
{

    // calculate miliamps
    sample.miliamps = SAMPLE2MAMPS(sample.Asamp);

    // 5V Standby is not measured in this configuration.
    // There are not enough ports to support all sensor boards. 
    // calculate volts
    switch (portNumber) {
	default :
        case 0:  // Read Vcc/Vref
            sample.Vsamp *= 64 ; // Perform Vsamp scaling
            sample.milivolts = (4096.0*65536)/sample.Vsamp ;
            sample.miliamps  = (4096.0*1024)/sample.Asamp ;
            break ;

        // RISER CARD GROUP
        case 1:    // J1, GPU1, 12V current sampled at Riser card 
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 2:    // J2, GPU1, 3.3V current sampled at Riser card 
	    sample.milivolts = SAMPLE_TO_3_3VOLTS (sample.Vsamp);
            break;
        case 3:    // J3, NIC1, 12V current sampled at Riser card 
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 4:    // J4, NIC1, 3.3V current sampled at Riser card 
	    sample.milivolts = SAMPLE_TO_3_3VOLTS (sample.Vsamp);
            break;

        // CPU/MEM GROUP
        case 5:    // J5, CPU1, 12V current sampled at MB socket 
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 6:    // J6, MEM1, 12V current sampled at MB socket 
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 7:    // J7, CPU2, 12V current sampled at MB socket 
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 8:    // J8, MEM2, 12V current sampled at MB socket 
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;

        // ATX & HDD GROUP
        case 9:    // J9, ATX MB socket, 12V current 
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 10:   // J10, ATX MB socket, 5V current     
	    sample.milivolts = SAMPLE_TO_5VOLTS(sample.Vsamp);
            break;
        case 11:   // J11, ATX MB socket, 3.3V current     
	    sample.milivolts = SAMPLE_TO_3_3VOLTS (sample.Vsamp);
            break;
        case 12:   // J12, HDD harness 12V
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 13:   // J13, HDD harness 5V
	    sample.milivolts = SAMPLE_TO_5VOLTS(sample.Vsamp);
            break;

        // PEG HARNESS GROUP
        case 14:   // J14, GPU1 PEG  harness 12V
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;
        case 15:   // J15, OPT_12V_PWR sampled at MB socket
	    sample.milivolts = SAMPLE_TO_12VOLTS(sample.Vsamp);
            break;

    }   // end switch()

    // calculate miliwatts
    sample.miliwatts = sample.miliamps * sample.milivolts;
    sample.miliwatts /= 1000;  // convert from E-6 to E-3

}   // end calcValues()


/***********************************************************/
int main(int argc, char *argv[])
{
    int i, portNumber ;
    int j ;
    int tmp[13];
    struct timeval start, now ;

  //  if(argc < 2)    { printUsage(argv[0]); }


    // Starting time
    gettimeofday( &start, NULL );

   // printf("\n%-4s %5s %5s %7s %7s %7s\n",
   //         "Pt#", "A", "V", "mA", "mV", "mW"); 

    // MAIN EXEC LOOP
    for(portNumber=1; portNumber<14; portNumber++) 
    { 
        //portNumber = atoi(argv[i+1]);
        if((portNumber < 0) || (portNumber > MAX_PORTNUM)) 
            { printUsage(argv[0]); }

        // What time is it now?
        gettimeofday( &now, NULL );

        // Collect raw readings
        getReadings(portNumber);

        // Calculate power
        calcValues(portNumber); 

        // Print results
if( 1 ) {
       // printf("%-4d %5d %5d %7d %7d %7d\n", 
       //     portNumber, sample.Asamp, sample.Vsamp/16,
       //     sample.miliamps,sample.milivolts,sample.miliwatts );
       tmp[portNumber-1] = sample.miliwatts;
} else {
        printf("%ld %ld.%06ld %-4d %5d %5d %7d %7d %7d\n", 
            start.tv_sec, now.tv_sec - start.tv_sec, now.tv_usec,
            portNumber, sample.Asamp, sample.Vsamp/16,
            sample.miliamps,sample.milivolts,sample.miliwatts );
};

    }  // end for() loop 
  
//for(portNumber=1; portNumber<14; portNumber++) printf("%7d \n", tmp[portNumber -1]);
    printf("%d %d %d %d %d %d \n", tmp[4], tmp[5], tmp[6], tmp[7] , tmp[11], tmp[12]);
    for( i = sizeof(devList)/sizeof(*devList) ; i >= 0 ; --i ) {
        if( devList[i].fd >= 0 ) {
            close( devList[i].fd );
        };
    };

    return (0);
}   // end main()
