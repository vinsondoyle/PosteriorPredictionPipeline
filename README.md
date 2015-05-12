
## Posterior Prediction Manual ##

This is an ongoing effort to produce a useful guide for posterior prediction. The pipeline outlined below is split into seven sections. There are scripts (bash & python) associated with each section that can be found here [[https://github.com/vinsondoyle/PosteriorPredictionPipeline]] or by contacting Vinson Doyle *vdoyle at agcenter.lsu.edu* or Jeremy Brown.

It is expected that you are starting with several nexus files with a ".nex" file extension. 

A few considerations before you begin: 
1) Removing all underscores and other punctuation from the base of all nexus filenames is easy to do and may simplify things downstream.
2) Posterior prediction is computationally intensive and can generate many output files, therefore it is worthwhile to separate the nexus files into subsets of about 150 grouped into separate directories.
3) Maintain a backup of your original nexus files somewhere.
4) Consider running through this pipeline with a couple genes before you jump into analyzing hundreds at once.
5) Make sure there are no subdirectories within your main directory containing all of the nexus files.

----

===Part A. Analyze empirical data with mrBayes 3.2.*===

Files needed for Part A:
-empirical data in nexus format [naming scheme: locus.nex]
-results from mrmodeltest (comparing 24 models) compiled into a single tab-delimited file (see "example_modeltable.txt")
-24 bayesblock files
-setupMB.sh
-wq.py
-wq_mb.sh
-wq_mb.pbs
-setGenSampfreq.sh (can be run pre or post-setup)

1. Setup folders with all necessary files to run empirical analyses

'''a''') Place all nexus files to be analyzed in base directory.====
                
'''b''') Make sure you have a tab delimited (not comma separated) file that lists the '''basename''' of each nexus file in the first column and the best-fit model in second column within the same directory as all the nexus files.
The models should be listed with a '+' between parameters and invariant sites before gamma distributed rates if both are present. For example, GTR, GTR+I, GTR+G, and GTR+I+G would be written in this way.  You will specify the tab delimited file as an argument to setupMB.sh. 
		
'''c''') Copy all 24 bayesblock files into the base directory. You can modify the settings for ngen and samplefreq with setGenSampfreq.sh either before or after running setup. The number of generations (ngen) and sampling frequency (samplefreq) are arguments, in that order, that must be passed to setGenSampfreq.sh. You must also specify if you are running post-setup or pre-setup with "post" or "pre" as the last argument.

To run before running the setup script (example with 10 million generations sampling every 10,000):

<code> ./setGenSampfreq.sh 10000000 10000 pre </code>

To run after running the setup script (example with 10 million generations sampling every 10,000):
<code> ./setGenSampfreq.sh 10000000 10000 post </code>

'''d''') Run setupMB.sh script. Remember, you must specify the model table file. If you are running everything under the same model and are annoyed by the need to specify a model table file, you can run genericModelTable.sh to generate such as file (see usage instructions in genericModelTable.sh).

To run set everything up for the empirical analyses:
<code> ./setupMB.sh example_modeltable.txt </code>

If you have to run setupMB.sh again for some reason, be sure to delete empDataList first.

		
2. Run empirical analyses with mrBayes3.2.*

'''a''') Make sure that empDataList (created by setupMB.sh), wq_mb.pbs, wq_mb.sh, and wq.py are all in the main directory.
		
'''b''') empDataList is a text file with the absolute file paths to each data file to be executed by MrBayes (*bayesblock). MAKE SURE THAT setupMB.sh HAS CREATED ALL THE DIRECTORIES!! The number of lines in empDataList <code> wc -l empDataList </code> should be the same as <code> ls -d */ | wc -l </code>  If you run the analysis in step C below and it does not complete in the alloted wall time, you will have to generate a new data list that includes only those not run previously. Better to get some idea for how long each run will take and allot enough walltime to start.

'''c''') <code> qsub wq_mb.pbs </code>
If you are running 4 runs with 4 chains each, it will only be necessary to modify the wq_mb.pbs file. In addition to changing the standard PBS flags appropriately, change the WORKDIR variable to the absolute path to the main directory. Make sure that the FILES variable is set to read empDataList.
	 		
			If you are running fewer runs or chains, it will be more efficient to change some variables in both wq_mb.sh and wq_mb.pbs:
				1) If you are running fewer than a total of 16 chains, modify the PROCS variable to a factor of 16 in wq_mb.sh.
				2) If you are running fewer than a total of 16 chains, modify the WPN variable to 16 divided by the number of PROCS.
		
3. Check to see if all tasks were executed. You can check the output file specified in wq_mb.pbs (#PBS -o). For example: <code> grep "True" outputFile | wc -l </code>  should equal the number of empirical nexus files. You may also want to confirm that the expected number of generations were completed for each analysis by checking the number of lines in one of the .p files for each empirical dataset.
