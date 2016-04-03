#!/usr/bin/env python
# encoding: utf-8
from __future__ import division
import sys
import os
import getopt
# import logging
import traceback
import time
# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)-5s %(module)-8s %(lineno)-3d - %(message)s")
# logger = logging.getLogger(__name__)
# logger.disabled = True
# from time import asctime, localtime
from pprint import pprint
import subprocess


# import mgf

def terminal(commandline, stdin=None, cwd=None):
    if isinstance(commandline,list): commandlist = commandline
    # else : commandlist = shlex.split(commandline)
    else : commandlist = commandline.split(' ')
    # print commandlist
    # print ' '.join(commandlist)
    startupinfo = subprocess.STARTUPINFO()
    p = subprocess.Popen(commandlist,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        startupinfo = subprocess.STARTUPINFO())
    # p.stdin.close() # http://mail.python.org/pipermail/python-bugs-list/2007-January/036901.html
    # return p.communicate() # stdout,stderr
    if stdin:
        stdout,stderr = p.communicate(input=stdin)
    else:
        p.stdin.close() # http://mail.python.org/pipermail/python-bugs-list/2007-January/036901.html
        stdout,stderr = p.communicate()
    return stdout,stderr
    
def MgfIterator(handle):
    # Dmgf= {}
    with open(mgffilename_in) as f:
        isEOF = False
        MS2_counter = 1 # 
        while not isEOF:
            line = f.readline()
            if line == "":
                isEOF = True
            elif "BEGIN IONS" in line:
                isENDIONS = False
                Dspectrum = {}
                Dspectrum['index'] = MS2_counter
                MS2_counter += 1
                Dspectrum['peakList'] = []
                while not isENDIONS:
                    line = f.readline()
                    
                    if "TITLE" in line:
                        Dspectrum["TITLE"] = line.rstrip().split('=')[1]
                    elif "SCANS" in line:
                        Dspectrum["SCANS"] = line.rstrip().split('=')[1]
                    elif "CHARGE" in line:
                        Dspectrum["CHARGE"] = line.rstrip().split('=')[1]
                    elif "PEPMASS" in line:
                        Dspectrum["PEPMASS"] = line.rstrip().split('=')[1]
                    elif "RTINSECONDS" in line:
                        Dspectrum["RTINSECONDS"] = line.rstrip().split('=')[1]
                    elif line == "\n":
                        pass
                    elif "END IONS" in line:
                        # Dmgf[ Dspectrum["SCANS"] ] = Dspectrum
                        isENDIONS = True
                        yield Dspectrum
                    else:
                        Dspectrum['peakList'].append( line.rstrip().split() )
    
if __name__ == "__main__":

    def usage():
        print
        print "Usage:\n"
        print 'python', __file__, '--in file.mgf [--out file_msmsevaled.mgf] --params msmsEval.params --nbspectra 500 [--msconvert path/to/msconvert.exe] [--msmseval path/to/msmsEval.exe] '
        print
        print 'python', __file__, '-i file.mgf [-o file_msmsevaled.mgf] -p msmsEval.params -n 500 [-c path/to/msconvert.exe] [-e path/to/msmsEval.exe] '
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],'hc:e:i:o:p:n:',['help','msconvert=','msmseval=','in=','out=','params=','nbspectra='])
    except getopt.GetoptError, err:
        print str(err)
        sys.exit(2)
        
    if not opts and not args: 
        sys.exit(usage())
    
    mgffilename_out = None
    MSCONVERT = None
    MSMSEVAL = None
    for o, a in opts:
        if o in ("-h", "--help"):
            sys.exit(usage())
        elif o in ("-c", "--msconvert"):
            MSCONVERT = os.path.abspath(a)
        elif o in ("-e", "--msmseval"):
            MSMSEVAL = os.path.abspath(a)
            
        elif o in ("-i", "--in"):
            mgffilename_in = os.path.abspath(a)
        elif o in ("-o", "--out"):
            mgffilename_out = os.path.abspath(a)
        elif o in ("-p", "--params"):
            msmsEval_params = os.path.abspath(a)
        elif o in ("-n", "--nbspectra"):
            NB_CONSERVED_SPECTRA = int(a)
        else:
            usage()
            sys.exit()
            
    if not mgffilename_out:
        mgffilename_out = os.path.splitext(mgffilename_in)[0] + '_msmsevaled.mgf'
    if not MSCONVERT:
        MSCONVERT = 'msconvert.exe'
    if not MSMSEVAL:
        MSMSEVAL = os.path.abspath('./msmsEval.exe')

    class Tee(object):
        def __init__(self, name, mode):
            self.file = open(name, mode)
            self.stdout = sys.stdout
            sys.stdout = self
        def __del__(self):
            sys.stdout = self.stdout
            self.file.close()
        def write(self, data):
            self.file.write(data)
            self.stdout.write(data)
            
    start = time.time()
    tee = Tee(mgffilename_out+'.log', 'wb')
    print ' '.join(sys.argv)
    print 
    print 'opts :'
    pprint(opts, width=160)
    print 'args :'
    pprint(args, width=160)
    print
    ################# Check the number of MS2 in the mgffilename_in
    mgffileIterator = MgfIterator(open(mgffilename_in))
    MS2_counter = 0
    for Dspectrum in mgffileIterator:
        MS2_counter += 1
    if MS2_counter <= NB_CONSERVED_SPECTRA:
        print "%d spectra in %s and %d requested : no need to filter with msmsEval" % (MS2_counter, mgffilename_in, NB_CONSERVED_SPECTRA )
        print "Renaming %s to %s" % (mgffilename_in, mgffilename_out )
        try:
            os.rename(mgffilename_in, mgffilename_out)
        except:
            print traceback.format_exc()
        print "OK"
        sys.exit()
    else:
        print "%d spectra in %s and %d requested" % (MS2_counter, mgffilename_in, NB_CONSERVED_SPECTRA )
    #################
    
    
    commandlist = [MSCONVERT, '--mzXML', mgffilename_in]
    print ' '.join(commandlist), '\n'
    stdout,stderr = terminal(commandlist, cwd=os.path.dirname(mgffilename_in))
    mzXMLfilename = os.path.splitext(mgffilename_in)[0] + '.mzXML'
    print 'elapsed time : %.2f min ' % ( (time.time() - start) / 60.0 )


    # msmsEval only accepts mzXML
    commandlist = [MSMSEVAL, '-s', mzXMLfilename, '-d', msmsEval_params ]
    print ' '.join(commandlist), '\n'
    stdout,stderr = terminal(commandlist, cwd=os.path.dirname(mgffilename_in))
    os.remove(mzXMLfilename)
    print 'elapsed time : %.2f min ' % ( (time.time() - start) / 60.0 )
    
    csvfilename = mzXMLfilename + '_eval.csv'
    indexScan2expProb = {}
    with open(csvfilename) as f:
        f.readline() # avoid headers
        for line in f:
            line_splitted = line.split(',')
            indexScan2expProb[int(line_splitted[0])] = float(line_splitted[12])
            
    expProbs = indexScan2expProb.values()
    nb_spectra_total = len(expProbs)
    print 'nb_spectra_total', nb_spectra_total
    prob_threshold = 1.0
    # print 'prob_threshold', prob_threshold
    nb_conserved_spectra = len([prob for prob in expProbs if prob > prob_threshold])
    
    criterion = False
    
    step = 0.1
    relative_err = 0.05
    inf = NB_CONSERVED_SPECTRA*(1-relative_err)
    sup = NB_CONSERVED_SPECTRA*(1+relative_err)
    
    prob_threshold_path = []
    print '\t'.join( map(str, ['prob_threshold','nb_conserved_spectra','nb_spectra_total','% conserved spectra', '%d < nb_conserved_spectra < %d ?'% (inf, sup),  'step']) )
    print '\t'.join( map(str, [prob_threshold, nb_conserved_spectra, nb_spectra_total, "%.2f %%" % (nb_conserved_spectra/nb_spectra_total*100), criterion, step ]) )
    while not criterion:
        if prob_threshold < 0.0 :
            break

        if nb_conserved_spectra <= inf:
            if (prob_threshold - step) in prob_threshold_path:
                step = step /10
            prob_threshold = prob_threshold - step
        elif nb_conserved_spectra >= sup:
            if (prob_threshold + step) in prob_threshold_path:
                step = step /10
            prob_threshold = prob_threshold + step
        prob_threshold_path.append(prob_threshold)
        nb_conserved_spectra = len([prob for prob in expProbs if prob > prob_threshold])
        criterion =  ( inf < nb_conserved_spectra) and (nb_conserved_spectra < sup )
        print '\t'.join( map(str, [prob_threshold, nb_conserved_spectra, nb_spectra_total, "%.2f %%" % (nb_conserved_spectra/nb_spectra_total*100), criterion, step ]) )

    print 'elapsed time : %.2f min ' % ( (time.time() - start) / 60.0 )
    conserved_spectra = [index for index,prob in indexScan2expProb.iteritems() if prob > prob_threshold]
    mgffileIterator = MgfIterator(open(mgffilename_in))
    with open(mgffilename_out, 'wb') as f:
        for Dspectrum in mgffileIterator:
            if Dspectrum['index'] in conserved_spectra:
                print >>f, 'BEGIN IONS'
                print >>f, 'TITLE=%s' % Dspectrum["TITLE"]
                print >>f, 'SCANS=%s' % Dspectrum["SCANS"] 
                print >>f, 'CHARGE=%s' % Dspectrum["CHARGE"] 
                print >>f, 'PEPMASS=%s' % Dspectrum["PEPMASS"] 
                print >>f, 'RTINSECONDS=%s' % Dspectrum["RTINSECONDS"] 
                for mz,int in Dspectrum['peakList']:
                    print >>f, '%s %s' % (mz,int)
                print >>f, ''
                print >>f, 'END IONS'
                print >>f, ''

    print
    print 'MGF filtered file written to %s' % mgffilename_out
    del tee
    print 'elapsed time : %.2f min ' % ( (time.time() - start) / 60.0 )
    