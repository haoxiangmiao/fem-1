#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>

/*
 * layout is sign + 7 digits (including decimal point) + E + 3 digit exponent
 * (including sign)
 */

#define LINE 160		/* space for input line */
#define NUM_DIMS 4
#define NUM_CHARS 15	/* space for each value, plus a little */
#define HEADER_SIZE 3
#define NUM_VALS_PER_LINE 3
#define XDISP_START 10
#define YDISP_START 22
#define ZDISP_START 34
#define EXP_START 9
#define NUM_DISP_CHARS 12
#define MIN_VALUE 1E-30
#define MAX_VALUE 1E30

char *inFileName = "nodout", *outFileName = "dispN.dat";
int debug = 0;
int legacyNodes = 0;

char *usage[] = {
	"Usage: processDyna [options]\n",
	"Options:\n",
	"\t-d debug level               1 or 2\n",
	"\t-i input file\n",
	"\t-l                           print nodes for each time step\n",
	"\t-o output file\n",
	0};

int
main(int argc, char **argv)
{
FILE *nodout;
size_t lineLength = LINE;
char *buf;
char *ptr;
int numChars;
int timestepRead = 0;
int timestepCount = 0;
char nodeID[NUM_CHARS], *xdisp, *ydisp, *zdisp;
int numNodes;
float dispVals[NUM_VALS_PER_LINE], header[HEADER_SIZE];
double temp;
FILE *outptr;
int c, currStep;
int currLine = 0;
char *endptr;

	if (parseArgs(argc, argv) == -1) {
		fprintf(stderr, "got an error in arguments\n");
		for (c = 0; usage[c]; c++)
			fprintf(stderr, "%s", usage[c]);
		exit(EXIT_FAILURE);
		}

/* open input file */

	if ((nodout = fopen(inFileName, "r")) == NULL) {
		fprintf(stderr, "couldn't open input file %s\n", inFileName);
		exit(EXIT_FAILURE);
		}

/* allocate space for input buffer, and the x, y, z values */

	if ((buf = (char *) malloc(lineLength + 1)) == NULL) { 
		fprintf(stderr, "couldn't allocate space for line\n");
		exit(EXIT_FAILURE);
		}

	xdisp = (char *) malloc(NUM_CHARS);
	ydisp = (char *) malloc(NUM_CHARS);
	zdisp = (char *) malloc(NUM_CHARS);

	if (xdisp == NULL || ydisp == NULL || zdisp == NULL) {
		fprintf(stderr, "couldn't allocate space for disp vals\n");
		exit(EXIT_FAILURE);
		}

/* open output file */

	if ((outptr = fopen(outFileName, "wb")) == NULL) {
		fprintf(stderr, "couldn't open output file %s\n", outFileName);
		exit(EXIT_FAILURE);
		}

/*
 * get number of nodeIDs, timesteps. I tried to think of a way to avoid
 * reading the file twice, but unless I allocate space to store the entire
 * first timestep, I can't do that
 */

	doCount(nodout, &numNodes, &timestepCount);

/* have to rewind input file before reading data */

	if (fseek(nodout, 0, SEEK_SET) != 0) {
		fprintf(stderr, "couldn't seek input file\n");
		exit(EXIT_FAILURE);
		}

/* set and write header values */

	header[0] = numNodes;
	header[1] = NUM_DIMS;
	header[2] = timestepCount;

	if (fwrite(header, sizeof(float), HEADER_SIZE, outptr) != HEADER_SIZE) {
		fprintf(stderr, "failed to write header\n");
		exit(EXIT_FAILURE);
		}

/*
 * write out the node IDs. we always do this at the beginning of the converted
 * file
 */
	writeNodeIDs(outptr, numNodes);

/*
 * process the file for the x, y, and z values. I'm using the line that
 * starts with 'nodal' as the divider between time steps.
 */

	currStep = 0;

	while ((numChars = getline(&buf, &lineLength, nodout)) != -1) {

		if (debug == 2) {
			fprintf(stderr, "got %s\n", buf);
			fprintf(stderr, "numChars %d\n", numChars);
			}

		if (strstr(buf, "nodal") != NULL) {
			timestepRead = 1;
			if (currStep == timestepCount) break;
			currStep += 1;
			if (debug == 1) fprintf(stderr, "processing time step %d\n", currStep);
			if (legacyNodes == 1 && currStep > 1) {
				if (debug == 1) fprintf(stderr, "writing nodeIDs again\n");
				writeNodeIDs(outptr, numNodes);
				}
			continue;
			}

/*
 * if we've seen a line with 'nodal' in it, 'timestepRead' is nonzero and
 * we've started reading data for
 * a time step. if, however, the current line is empty, that means that we've
 * seen all the data for that time step. in that case, we proceed to the next
 * time step.
 */
		currLine++;
		if (timestepRead != 0) {
			if (numChars == 1) {	/* empty line */
				timestepRead = 0;
				currLine = 0;
				}
/*
 * use our knowledge of the line format to parse out the values. we already
 * have the number of node IDs, so we can ignore that here. we also
 * cut off all really small or really big values so we can save as float.
 */
			else {
				strncpy(xdisp, buf + XDISP_START, NUM_DISP_CHARS);
				xdisp[NUM_DISP_CHARS] = '\0';
				if ((ptr = strchr(xdisp, 'E')) == NULL) correctE(xdisp);
				temp = atof(xdisp);
				
				/*
				if (currStep == 2 && currLine > 3600000)
					fprintf(stderr, "input %s temp %e\n", xdisp, temp);
				 */
				 
				if (temp < 0) {
					if (fabs(temp) < MIN_VALUE) temp = -MIN_VALUE;
					else if (fabs(temp) > MAX_VALUE) temp = -MAX_VALUE;
					}
				else  {
					if (temp < MIN_VALUE) temp = MIN_VALUE;
					else if (temp > MAX_VALUE) temp = MAX_VALUE;
					}
				dispVals[0] = (float )temp;
			
			/*
				if (currStep == 2 && currLine > 3600000)
					fprintf(stderr, "temp %e, dispVal(x) %e\n", temp, dispVals[0]);
			 */

				strncpy(ydisp, buf + YDISP_START, NUM_DISP_CHARS);
				ydisp[NUM_DISP_CHARS] = '\0';
				if ((ptr = strchr(ydisp, 'E')) == NULL) correctE(ydisp);
				temp = atof(ydisp);
				if (temp < 0) {
					if (fabs(temp) < MIN_VALUE) temp = -MIN_VALUE;
					else if (fabs(temp) > MAX_VALUE) temp = -MAX_VALUE;
					}
				else  {
					if (temp < MIN_VALUE) temp = MIN_VALUE;
					else if (temp > MAX_VALUE) temp = MAX_VALUE;
					}
				dispVals[1] = (float )temp;

				strncpy(zdisp, buf + ZDISP_START, NUM_DISP_CHARS);
				zdisp[NUM_DISP_CHARS] = '\0';
				if ((ptr = strchr(zdisp, 'E')) == NULL) correctE(zdisp);
				temp = atof(zdisp);
				if (temp < 0) {
					if (fabs(temp) < MIN_VALUE) temp = -MIN_VALUE;
					else if (fabs(temp) > MAX_VALUE) temp = -MAX_VALUE;
					}
				else  {
					if (temp < MIN_VALUE) temp = MIN_VALUE;
					else if (temp > MAX_VALUE) temp = MAX_VALUE;
					}
				dispVals[2] = (float )temp;

/* write current values */
				if (fwrite(dispVals, sizeof(float), NUM_VALS_PER_LINE, outptr) != NUM_VALS_PER_LINE) {
					fprintf(stderr, "failed to write one of the data lines\n");
					exit(EXIT_FAILURE);
					}
				}
			}
		}

	free(buf);
	free(xdisp);
	free(ydisp);
	free(zdisp);

	fclose(nodout);

	fclose(outptr);
}

/*
 * fix the situation where we had a three digit negative exponent, and dyna
 * left the 'E' out. keep first nine chars, and append 'E-100'
 */

correctE(char *disp)
{
char *ptr;
int insertPos;


	if ((ptr = strchr(disp + 1, '-')) == NULL) {
		fprintf(stderr, "can't happen\n");
		exit(EXIT_FAILURE);
		}

	insertPos = EXP_START - 1;

/* strncpy copies null byte at end */

	strncpy(disp + insertPos, "E-100", 6);
}

doCount(FILE *inFilePtr, int *nodes, int *steps)
{
size_t lineLength = LINE;
char *buf;
int numChars;
int node;
int timestepRead = 0;
char nodeID[NUM_CHARS];
FILE *cmdPtr;
char result[1024];
char command[128];


/*
 * this makes a system call to grep to count the number of time steps in the
 * input file.
 */

	strcpy(command, "grep nodal ");
	strcat(command, inFileName);
	strcat(command, " | wc -l");
    cmdPtr = popen(command, "r");

	if (cmdPtr == NULL) {
		perror("popen");
		exit(EXIT_FAILURE);
		}

/*
 * going to always drop last time step since it's sometimes short; because
 * this version writes the data on the fly, there's no easy way to sometimes
 * drop the last step.
 */
	if (fgets(result, sizeof(result), cmdPtr)) {
		*steps = atoi(result) - 1;
		}


	pclose(cmdPtr);

	if (debug == 1) fprintf(stderr, "timestep count %d\n", *steps);

	if ((buf = (char *) malloc(lineLength + 1)) == NULL) { 
		fprintf(stderr, "couldn't allocate space for line in doCount\n");
		exit(EXIT_FAILURE);
		}

/* makes one pass through data; the last nodeID is the number of nodeIDs */

	while ((numChars = getline(&buf, &lineLength, inFilePtr)) != -1) {

		if (strstr(buf, "nodal") != NULL) {
			timestepRead = 1;
			continue;
			}
		if (timestepRead) {
			if (numChars == 1) {
				timestepRead = 0;
				*nodes = node;
				if (debug == 1) fprintf(stderr, "num nodes %d\n", *nodes);
				break;
				}
			else {
				strncpy(nodeID, buf, 10);
				nodeID[10] = '\0';
				node = atoi(nodeID);
				}
			}
		}
}

parseArgs(int argc, char **argv) {
int c;

	while ((c = getopt(argc, argv, "i:o:ld:")) != -1)
		switch(c) {
			case 'd':
				debug = atoi(optarg);
				break;
			case 'i':
				inFileName = optarg;
				break;
			case 'o':
				outFileName = optarg;
				break;
			case 'l':
				legacyNodes = 1;
				break;
			case '?':
				if (optopt == 'i')
					fprintf (stderr, "Option -%c requires an argument.\n", optopt);
				if (optopt == 'o')
					fprintf (stderr, "Option -%c requires an argument.\n", optopt);
				else if (isprint (optopt))
					fprintf (stderr, "Unknown option `-%c'.\n", optopt);
				else
					fprintf (stderr, "Unknown option character `\\x%x'.\n", optopt);
				return(-1);
			default:
				exit(EXIT_FAILURE);
			}

	return(0);
}

writeNodeIDs(FILE *ptr, int num)
{
int i;
float node;

	for (node = 1; node <= num; node++)
		if (fwrite(&node, sizeof(float), 1, ptr) != 1) {
			fprintf(stderr, "failed to write header\n");
			exit(EXIT_FAILURE);
			}
}
