
## Posterior Prediction Manual ##

This is an ongoing effort to produce a useful guide for posterior prediction. The pipeline outlined below is split into seven sections. There are scripts (bash & python) associated with each section that can be found here [https://github.com/vinsondoyle/PosteriorPredictionPipeline] or by contacting Vinson Doyle *vdoyle at agcenter.lsu.edu* or Jeremy Brown.

It is expected that you are starting with several nexus files with a ".nex" file extension. 

A few considerations before you begin: 
1) Removing all underscores and other punctuation from the base of all nexus filenames is easy to do and may simplify things downstream.
2) Posterior prediction is computationally intensive and can generate many output files, therefore it is worthwhile to separate the nexus files into subsets of about 150 grouped into separate directories.
3) Maintain a backup of your original nexus files somewhere.
4) Consider running through this pipeline with a couple genes before you jump into analyzing hundreds at once.
5) Make sure there are no subdirectories within your main directory containing all of the nexus files.

----

###Part A. Analyze empirical data with mrBayes 3.2.*###

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

a) Place all nexus files to be analyzed in base directory.====
                
b) Make sure you have a tab delimited (not comma separated) file that lists the '''basename''' of each nexus file in the first column and the best-fit model in second column within the same directory as all the nexus files.
The models should be listed with a '+' between parameters and invariant sites before gamma distributed rates if both are present. For example, GTR, GTR+I, GTR+G, and GTR+I+G would be written in this way.  You will specify the tab delimited file as an argument to setupMB.sh. 
		
c) Copy all 24 bayesblock files into the base directory. You can modify the settings for ngen and samplefreq with setGenSampfreq.sh either before or after running setup. The number of generations (ngen) and sampling frequency (samplefreq) are arguments, in that order, that must be passed to setGenSampfreq.sh. You must also specify if you are running post-setup or pre-setup with "post" or "pre" as the last argument.

To run before running the setup script (example with 10 million generations sampling every 10,000):

<code> ./setGenSampfreq.sh 10000000 10000 pre </code>

To run after running the setup script (example with 10 million generations sampling every 10,000):
<code> ./setGenSampfreq.sh 10000000 10000 post </code>

d) Run setupMB.sh script. Remember, you must specify the model table file. If you are running everything under the same model and are annoyed by the need to specify a model table file, you can run genericModelTable.sh to generate such as file (see usage instructions in genericModelTable.sh).

To run set everything up for the empirical analyses:
<code> ./setupMB.sh example_modeltable.txt </code>

If you have to run setupMB.sh again for some reason, be sure to delete empDataList first.

		
2. Run empirical analyses with mrBayes3.2.*

a) Make sure that empDataList (created by setupMB.sh), wq_mb.pbs, wq_mb.sh, and wq.py are all in the main directory.
		
b) empDataList is a text file with the absolute file paths to each data file to be executed by MrBayes (*bayesblock). MAKE SURE THAT setupMB.sh HAS CREATED ALL THE DIRECTORIES!! The number of lines in empDataList <code> wc -l empDataList </code> should be the same as <code> ls -d */ | wc -l </code>  If you run the analysis in step C below and it does not complete in the alloted wall time, you will have to generate a new data list that includes only those not run previously. Better to get some idea for how long each run will take and allot enough walltime to start.

c) <code> qsub wq_mb.pbs </code>
If you are running 4 runs with 4 chains each, it will only be necessary to modify the wq_mb.pbs file. In addition to changing the standard PBS flags appropriately, change the WORKDIR variable to the absolute path to the main directory. Make sure that the FILES variable is set to read empDataList.
	 		
If you are running fewer runs or chains, it will be more efficient to change some variables in both wq_mb.sh and wq_mb.pbs:
1) If you are running fewer than a total of 16 chains, modify the PROCS variable to a factor of 16 in wq_mb.sh.
2) If you are running fewer than a total of 16 chains, modify the WPN variable to 16 divided by the number of PROCS.


3. Check to see if all tasks were executed. You can check the output file specified in wq_mb.pbs (#PBS -o). For example: <code> grep "True" outputFile | wc -l </code>  should equal the number of empirical nexus files. You may also want to confirm that the expected number of generations were completed for each analysis by checking the number of lines in one of the .p files for each empirical dataset.

###Part B. Check for convergence and determine burnin for subsampling###

This part assumes that you have run your empirical analyses as described above and did not use MrConverge to monitor MrBayes runs. Here you will use MrConverge (distributed by Alan Lemmon) to check for convergence and determine burnin in order to subsample from the posterior distribution for posterior predictive simulations.

<br>Files needed for Part B:<br />
*mrc.conblock (generic file: make sure nruns is set appropriately and filename is set to "data")<br />
*MrConverge1b2.5.jar (you need this version to use EVALB option)<br />
*mrc_convergenceSetup.sh<br />
*mrc_convergenceSetup.pbs<br />
*wq_mrc.pbs<br />
*wq_mrc.sh<br />
*wq.py<br />
*checkConvergence.py<br />
*batchCheckConvergence.sh<br />
*batchCheckConvergence.pbs<br />

<br>Optional Files:<br />
batchMRC.sh - this is written to utilize the 12 processors on the linux box in A248. This is an alternative to running the wq scripts above. If you want to run it on a different machine, just make sure you change "12" on line 15 to equal the number of processors on your machine.<br />
<br> <br />
'''1. Create a list of file paths to the directories containing your empirical analyses''' (a - "empDataDirectories") and the paths to the mrc.conblock files (b - "MRCDataList"). <br />
*'''a''')  Assuming you have a file called "empDataList" that list the paths to your bayesblock files, to create your empDataDirectories file: <code> for f in $(cat empDataList); do dirN=`dirname $f`; echo $dirN"/" >> empDataDirectories; done </code>

*'''b''')  Assuming you have a file called "empDataList" that list the paths to your bayesblock files, to create your MRCDataList file: <code> for f in $(cat empDataList); do dirN=`dirname $f`; echo $dirN"/mrc.conblock" >> MRCDataList; done </code>

'''2. Make sure you have all of the files necessary to setup for MrConverge.''' Modify the mrc.conblock file to make sure that "nruns" is set to the number used for the empirical analyses and "filename=data;" and place in the main directory.  Make sure that MrConverge1b2.5.jar is in the main directory.

'''3. Setup for MrConverge.''' Assuming you have the following files in your main directory: mrc.conblock (modified as specified above), MrConverge1b2.5.jar, mrc_convergenceSetup.sh, mrc_convergenceSetup.pbs: <code> qsub mrc_convergenceSetup.pbs </code>

Step 3 will renames the empirical .p and.t files so that they can be read by MrConverge, modify the mrc.conblock file appropriately and place in the respective directories, place MrConverge in the correct place for each analysis below.

'''4. Run MrConverge with''' <code> qsub wq_mrc.pbs </code> 

Alternatively, you can use batchMRC.sh to run it on the linux box in LSB248.

'''5. Check to make sure that all tasks ran.''' Wait for step 4 to complete then, using the same approach as in A4 above, check that all tasks were submitted by wq.

6. Check that all empirical analyses have converged. <br />
*'''a''') Generate list of paths to mrconverge.log files: <code> for f in $(cat empDataDirectories); do echo $f"mrconverge.log" >> MRCLogList; done </code>

*'''b''') Make sure that checkConvergence.py, batchCheckConvergence.sh, and batchCheckConvergence.pbs are all in the main directory.

*'''c''') <code> qsub batchCheckConvergence.pbs </code>

*'''d''') step 3 will generate a text file ("notConverged.txt"). If the MaxBppCI for the statistic corresponding to the maximum Opt Burn value is greater than 0.1 then the MaxBppCI and the path to the mrconverge.log file will be output to this file. This indicates that these runs may not have converged. If there is nothing in "notConverged.txt", then all runs appear to have converged and you can move on to subsampling and simulating posterior predictive datasets.

###Part C. Simulate posterior predictive datasets###

<br>Files needed for Part C:<br />
*subsamplerBurn3.2.sh<br />
*stationarySubsamplev2.2.sh '''OR''' stationarySubsamplev2.4.sh - the former is for nruns=2 and the latter nruns=4 (to be made more flexible in the future)<br />
*stationarySubsample.pbs<br />
*PuMAv0.907c.jar<br />
*seq-gen (compiled on the appropriate system)<br />
*puma.in (generic file - So that the batchPuma.sh runs properly, make sure these parameters are set as such: datfile=data.nex; logfile=data; conblockfile=data.conblock; bayesblockfile=data.bayesblock;)<br />
*batchPuma.sh<br />
*addBatchMissPatterns.sh<br />
*repMissPatternsVD.py<br />
*ctSubTrees.sh<br />

<br>Optional Files:<br />
*subsampler_oops.sh - cleans up after step 1 below if the number of trees is not 100<br />
*batchPumaCleanup.sh<br />
<br> <br />

'''1. Make sure stationarySubsamplev2.2.sh (or ...2.4.sh, see above), stationarySubsample.pbs, subsamplerBurn3.2.sh are all in the base directory.'''<br />

'''2. Sample a total of 100 trees and associated parameter values from empirical stationary distribution.'''<br />
*<code>qsub stationarySubsample.pbs</code>

'''3. Check to make sure you have subsampled 100 trees.'''<br />
*<code> ./ctSubtrees.sh</code><br />
*If there are 100 total trees across all .t files in each empDataDirectory, then there will not be any output and all is well. Move on.<br />
*If there are '''not''' 100 total trees across all .t files in each empDataDirectory, then figure out the problem and run subsampler_oops.sh to reset everything so you can run qsub stationarySubsample.pbs again.<br />
'''4. Setup for simulating posterior predictive data.''' Make sure PuMAv0.907c.jar, generic puma.in file, and seq-gen are all in the base directory. Important: make sure you have compiled seq-gen on the particular system you are using.<br />
*<code> ./batchPumaSetup.sh</code><br />
'''5. Enable the use of the GUI required by PuMA.''' This is done on SuperMike-II by logging out (<code> exit </code>) and logging back in with x-forwarding <code>ssh -X username@hostname</code><br />
'''6. Initiate an interactive session with x-forwarding:''' <code>qsub -I -l nodes=1:ppn=16 -l walltime=04:00:00 -X -A ''allocation''</code><br />
*Replace ''allocation'' with the appropriate allocation code.<br /><br />
*Make sure you have XQuartz installed locally or failure is assured.<br />
'''7. Run PuMA:''' <code>./batchPumaInteractive.sh</code><br />
'''8. Add indels into simulated data to match patterns in empirical data.'''<br />
*'''a'''). Terminate the interactive session<br />
*'''b'''). Make sure repMissPatternsVD.py and addBatchMissPatterns.sh are in the main directory.<br />
*'''c'''). <code>qsub addBatchMissPatterns.pbs</code><br />


###Part D. Analyze posterior predictive datasets with MrBayes###

'''Important note:'''<br /> 
It might be worthwhile to split your analyses into smaller subsets. One (preferred) way to do this is to split your empDataDirectories file into smaller sets. You can do this with the following which will split your empDataDirectories file into sets of 350 lines each and name them empDataDirectories'''aa''', empDataDirectories'''ab''', etc.: <code>split -l 350 empDataDirectories empDataDirectories</code><br />
Then, make directories to put these subsets: <code>mkdir set_a set_b</code><br />
Now move the empirical directories into the newly created directories: <br />
<code>for f in $(cat empDataDirectoriesaa); do mv $f set_a; done</code><br />
<code>for f in $(cat empDataDirectoriesab); do mv $f set_b; done</code><br />
<code>mv empDataDirectoriesaa set_a</code><br />
<code>mv empDataDirectoriesab set_b</code><br />

Alternatively, you could divide the PPDataList (see below) into several separate files of perhaps 5000 lines each and setup multiple wq_mb.pbs files. This is another way you may be able to run several analyses simultaneously and make it thru the list of PP datafiles more efficiently. Alternatively, you can start an analysis with the PPDataList as the input file. After the run has reached the walltime or will not execute any additional tasks because it is expected they will not complete before the walltime is up, you can extract the file names for those that did not run successfully from the output file of the original run and save them into a separate file using the bash commands below.

<br>Files needed for Part D:<br />
*setupPP_mb.sh<br />
*setupPP_mb.pbs<br />
*genFileList_PP.sh<br />
*wq_mb.pbs<br />
*wq_mb.sh<br />
*wq.py<br />

'''1. Setup folders, transfer appropriate bayesblock files and nexus files into those folders.'''<br />
'''Two things to check:''' <br />
**This assumes there is a line of the following format in a file ending in ".bb", which is your bayes block file: "mcmc ngen=someNumber samplefreq=someNumber nruns=someNumber nchains=someNumber;"
**Make sure there is only one file in each empirical data directory that ends in ".bb" <br />
**You must specify the empDataDirectories filename (argument1), the number of generations for each posterior predictive analysis (argument2), the sample frequency (argument3), the number of runs for each analysis (argument4), the number of mcmc chains per analysis (argument5). <br />
For example, the following, which should be specified in setupPP_mb.pbs, would setup your posterior predictive runs to be run for 1 million generations, sampling everying 500, 2 independent runs, and 4 mcmc chains per run: <code>./setupPP_mb.sh empDataDirectories 1000000 500 2 4</code><br />
*'''a'''). Run setupPP_mb.sh - this will setup the posterior predictive datasets to be analyzed.<br />
<code>qsub setupPP_mb.pbs</code><br />
**Check setupPP_mb (PBS output file) to see if the script ran up to the walltime. If it does not finish, you can simply run it again and it will skip over any that have been fully setup for further analysis.<br />

'''2. Analyze posterior predictive datasets with MrBayes'''<br />
*'''a'''). Make sure wq_mb.pbs, wq_mb.sh, and wq.py are all in the main directory (set_a, set_b, etc.).
*'''b'''). Change into main directory and generate a list of the absolute file paths to each posterior predictive directory that contains the bayesblock (.bb) file and the simulated nexus file: <code>cd set_a && for f in $(cat empDataDirectoriesaa); do baseN=`basename $f`; lst=$(ls -d $f"SeqOutfiles/"*/); for n in $lst; do echo $n$baseN".bb" >> PPDataList; done; done </code><br />
*'''c'''). Run analyses with wq (don't forget to adjust accordingly). Review PartA2 above for a refresher on wq, read the manual, or contact Vinson. <code>qsub wq_mb.pbs</code><br />

###Part E. Use MrConverge to check convergence and find the appropriate burnin for AMP###

Files needed for Part E:
*setupPPredMrc_convergence.pbs<br />
*setupPPredMrc_convergence.sh<br />
*mrc.conblock<br />
*wq_mrc.pbs<br />
*wq_mrc.sh<br />
*wq.py<br />
*fileCleanupAfterPP_MRC.pbs<br />
*fileCleanupAfterPP_MRC.sh<br />

Optional Files:<br />
*genFileList_PPMRC.sh<br />

'''1. Make sure you have all of the files in the right place and they are set appropriately'''<br />
*'''a'''). mrc.conblock and MrConverge1b2.5.jar should be in the main directory. <br />
*'''b'''). Check the *conblock file to make sure that nruns is set to the number of runs that you actually ran for each PP dataset.<br />

'''2. this will run setupPPredMrc_convergence.sh'''<br /> 
<code>qsub setupPPredMrc_convergence.pbs</code><br />
'''3. Generate a text file (called PP_MRCDataList) with absolute file paths to the mrc.conblock file which is the input for MrConverge. Do this by using PPDataList (or whatever you called the file with the absolute file paths to your posterior predictive datasets above) as a template:'''<br />
<code>for p in $(cat PPDataList); do dirN=`dirname $p`; echo $dirN"/mrc.conblock" >> PP_MRCDataList; done</code><br />
'''4. Run MrConverge with wq_mrc - you should only need to modify the WORKDIR variable in wq_mrc.pbs'''<br />
<code>qsub wq_mrc.pbs</code><br />
'''5. Cleanup extraneous files after running wq_mrc so as not to exceed disk quota and speed up the rsync process.'''<br />
<code>qsub fileCleanupAfterPP_MRC.pbs</code><br />
