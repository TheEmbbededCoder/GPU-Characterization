#include "hip/hip_runtime.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "../lcutil.h"


#define COMP_ITERATIONS (4096) //512
#define REGBLOCK_sizeB (4)
#define UNROLL_ITERATIONS (32)
#define THREADS_WARMUP (1024)
int THREADS;
int BLOCKS;
#define deviceNum (0)


//CODE
__global__ void warmup(int aux){

	__shared__ double shared[THREADS_WARMUP];

	short r0 = 1.0,
		  r1 = r0+(short)(31),
		  r2 = r0+(short)(37),
		  r3 = r0+(short)(41);

	for(int j=0; j<COMP_ITERATIONS; j+=UNROLL_ITERATIONS){
		#pragma unroll
		for(int i=0; i<UNROLL_ITERATIONS; i++){
			// Each iteration maps to doubleing point 8 operations (4 multiplies + 4 additions)
			r0 = r0 * r0 + r1;//r0;
			r1 = r1 * r1 + r2;//r1;
			r2 = r2 * r2 + r3;//r2;
			r3 = r3 * r3 + r0;//r3;
		}
	}
	shared[threadIdx.x] = r0;
}

template <class T> __global__ void benchmark(T* cdin,  T* cdout){

	const long ite=blockIdx.x * THREADS + threadIdx.x;

	register T r0;

	r0=cdin[ite];
	cdout[ite]=r0;
}

void initializeEvents(hipEvent_t *start, hipEvent_t *stop){
	HIP_SAFE_CALL( hipEventCreate(start) );
	HIP_SAFE_CALL( hipEventCreate(stop) );
	HIP_SAFE_CALL( hipEventRecord(*start, 0) );
}

double finalizeEvents(hipEvent_t start, hipEvent_t stop){
	HIP_SAFE_CALL( hipGetLastError() );
	HIP_SAFE_CALL( hipEventRecord(stop, 0) );
	HIP_SAFE_CALL( hipEventSynchronize(stop) );
	float kernel_time;
	HIP_SAFE_CALL( hipEventElapsedTime(&kernel_time, start, stop) );
	HIP_SAFE_CALL( hipEventDestroy(start) );
	HIP_SAFE_CALL( hipEventDestroy(stop) );
	return kernel_time;
}

void runbench_warmup(){
	const int BLOCK_sizeB = 256;
	const int TOTAL_REDUCED_BLOCKS = 256;
    int aux=0;

	dim3 dimBlock(BLOCK_sizeB, 1, 1);
	dim3 dimReducedGrid(TOTAL_REDUCED_BLOCKS, 1, 1);

	hipLaunchKernelGGL((warmup), dim3(dimReducedGrid), dim3(dimBlock ), 0, 0, aux);
	HIP_SAFE_CALL( hipGetLastError() );
	HIP_SAFE_CALL( hipDeviceSynchronize() );
}

void runbench(double* kernel_time, double* flops, int * hostIn, int * hostOut){

	hipEvent_t start, stop;
	dim3 dimBlock(THREADS, 1, 1);
	dim3 dimGrid(BLOCKS, 1, 1);

	initializeEvents(&start, &stop);

    hipLaunchKernelGGL((benchmark<int>), dim3(dimGrid), dim3(dimBlock), 0, 0, (int *) hostIn, (int *) hostOut);

	hipDeviceSynchronize();

	double time = finalizeEvents(start, stop);
	
	*kernel_time = time;
}

int main(int argc, char *argv[]){

	int i;
	int device = 0;

	hipDeviceProp_t deviceProp;

	int ntries;
	unsigned int sizeB, size; 
	if (argc > 2) {
		sizeB = atoi(argv[1]);
		ntries = atoi(argv[2]);
	}
	else if(argc > 1) {
		sizeB = atoi(argv[1]);
		ntries = 1;
	}
	else {
		printf("Usage: %s [buffer sizeB kBytes] [ntries]\n", argv[0]);
		exit(1);
	}

	// Computes the total sizeB in bits
	sizeB *= 1024;
	size = sizeB/(int)sizeof(int);

	if(sizeB >= 1024) {
		if(sizeB % 1024 != 0) {
			printf("sizeB not divisible by 1024!!!\n");
			exit(1);
		}
	}

	hipSetDevice(deviceNum);

	double n_time[ntries][2], value[ntries][4];


	// DRAM Memory Capacity
	size_t freeCUDAMem, totalCUDAMem;
	HIP_SAFE_CALL(hipMemGetInfo(&freeCUDAMem, &totalCUDAMem));

	HIP_SAFE_CALL(hipGetDeviceProperties(&deviceProp, device));

	// Kernel Config
	if(size < 1024) {
		THREADS = size;
		BLOCKS = 1;
	}
	else {
		THREADS = 1024;
		BLOCKS = size/1024;
	}	

	printf("size %d sizeB %d\n", size, sizeB);
	printf("THREADS %d BLOCKS %d\n", THREADS, BLOCKS);

	// Initialize Host Memory
	int *hostIn = (int *) malloc(sizeB);
	int **hostOut = (int **) malloc(10 * sizeof(int*));
	for (int i = 0; i < 10; ++i)
	{
		hostOut[i] = (int *) calloc(size, sizeof(int));
	}

	// Generates array of random numbers
    srand((unsigned) time(NULL));
    int sum = 0;
	int random = 0;
	// Initialize the input data
	for (i = 0; i < size-1; i++) {
		random = ((unsigned)rand() << 17) | ((unsigned)rand() << 2) | ((unsigned)rand() & 3);
		hostIn[i] = random;
		sum += random;
	}
	// Places the sum on the last vector position
	hostIn[i] = sum;

	// Initialize Host Memory
	int *deviceIn;
	int *deviceOut;
	HIP_SAFE_CALL(hipMalloc((void**)&deviceIn, size * sizeof(int)));
	HIP_SAFE_CALL(hipMalloc((void**)&deviceOut, size * sizeof(int)));

	// Synchronize in order to wait for memory operations to finish
	HIP_SAFE_CALL(hipDeviceSynchronize());

	hipEvent_t start, stop;
	initializeEvents(&start, &stop);

	// Transfer data from host to device
	HIP_SAFE_CALL(hipMemcpy(deviceIn, hostIn, size*sizeof(int), hipMemcpyHostToDevice));
	// Synchronize in order to wait for memory operations to finish
	HIP_SAFE_CALL(hipDeviceSynchronize());

	double MemCpyTime = finalizeEvents(start, stop);
	
	// Resets the DVFS Settings
	int status = system("rocm-smi -r");
	status = system("./DVFS -P 7");
	status = system("./DVFS -p 3");

	for (i=0;i<1;i++){
		runbench_warmup();
	}
	for (i=0;i<ntries;i++){
		runbench(&n_time[0][0],&value[0][0], deviceIn, deviceOut);
		printf("Registered time: %f ms\n", n_time[0][0]);
	}

	// Synchronize in order to wait for memory operations to finish
	HIP_SAFE_CALL(hipDeviceSynchronize());

	// Transfer data from device to host
	HIP_SAFE_CALL(hipMemcpy(hostOut[0], deviceOut, size*sizeof(int), hipMemcpyDeviceToHost));

	// Synchronize in order to wait for memory operations to finish
	HIP_SAFE_CALL(hipDeviceSynchronize());

	HIP_SAFE_CALL(hipDeviceReset());

	printf("Total GPU memory %lu, free %lu\n", totalCUDAMem, freeCUDAMem);
	printf("Buffer sizeB: %luMB\n", size*sizeof(int)/(1024*1024));
	printf("MemCpyTime %f ms\n", MemCpyTime);

	// Verification of data transfer
	int sum_received = 0;
	for (i = 0; i < size-1; i++) {
		sum_received += hostOut[0][i];
	}
	printf("Result: ");
	if(sum == sum_received && sum == hostOut[0][size-1]) {
		printf("Correct\n");
	}
	else {
		printf("Incorrect\n");
	}

	free(hostIn);
	for (int i = 0; i < 10; ++i){
		free(hostOut[i]);
	}
	free(hostOut);
	return 0;
}