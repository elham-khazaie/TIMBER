import CMS_lumi
import ROOT, collections
from collections import OrderedDict
from TIMBER.Analyzer import HistGroup

def StitchQCD(QCDdict,normDict=None):
    '''Stitches together histograms in QCD hist groups.

    Args:
        QCDdict ({string:HistGroup}): Dictionary of HistGroup objects
        normDict ([string:float]): Default to None and assume normalization has already been done.
            Factors to normalize each sample to where keys must match QCDdict keys.
    Returns:
        New HistGroup with histograms in group being the final stitched versions
    '''
    # Normalize first if needed
    if normDict != None:
        for k in normDict.keys():
            for hkey in QCDdict[k].keys():
                QCDdict[k][hkey].Scale(normDict[k])
    # Stitch
    out = HistGroup("QCD")
    for ksample in QCDdict.keys(): 
        for khist in QCDdict[ksample].keys():
            if khist not in out.keys():
                out[khist] = QCDdict[ksample][khist].Clone()
            else:
                out[khist].Add(QCDdict[ksample][khist])

    return out

def CompareShapes(outfilename,year,prettyvarname,bkgs={},signals={},names={},colors={},scale=True,stackBkg=False):
    '''Create a plot that compares the shapes of backgrounds versus signal.
       Backgrounds will be stacked together and signals will be plot separately.
       Total background and signals are scaled to 1 if scale = True. Inputs organized 
       as dicts so that keys can match across dicts (ex. bkgs and bkgNames).

    Args:
        outfilename (string): Path where plot will be saved.
        prettyvarname (string): What will be assigned to as the axis title.
        bkgs ({string:TH1}, optional): . Defaults to {}.
        signals ({string:TH1], optional): [description]. Defaults to {}.
        names ({string:string}, optional): Formatted version of names for backgrounds and signals to appear in legend. Keys must match those in bkgs and signal. Defaults to {}. 
        colors ({string:int}, optional): TColor code for backgrounds and signals to appear in plot. Keys must match those in bkgs and signal. Defaults to {}.
        scale (bool, optional): Scales everything to unity if true. Defaults to True.
    '''
    # Initialize
    c = ROOT.TCanvas('c','c',800,700)
    legend = ROOT.TLegend(0.6,0.72,0.87,0.88)
    legend.SetBorderSize(0)
    ROOT.gStyle.SetTextFont(42)
    ROOT.gStyle.SetOptStat(0)
    if stackBkg:
        bkgStack = ROOT.THStack('Totbkg','Total Bkg - '+prettyvarname)
        bkgStack.SetTitle(';%s;%s'%(prettyvarname,'A.U.'))
         # Add bkgs to integral
        for bkey in bkgs.keys():
            tot_bkg_int += bkgs[bkey].Integral()

    tot_bkg_int = 0
    if colors == None:
        colors = {'signal':ROOT.kBlue,'qcd':ROOT.kYellow,'ttbar':ROOT.kRed,'multijet':ROOT.kYellow}
        
    if scale:
        # Scale bkgs to total integral
        for bkey in bkgs.keys():
            if stackBkg: bkgs[bkey].Scale(1.0/tot_bkg_int)
            else: bkgs[bkey].Scale(1.0/bkgs[bkey].Integral())
        # Scale signals
        for skey in signals.keys():
            signals[skey].Scale(1.0/signals[skey].Integral())

    # Now add bkgs to stack, setup legend, and draw!
    colors_in_legend = []
    procs = OrderedDict() 
    procs.update(bkgs)
    procs.update(signals)
    for pname in procs.keys():
        h = procs[pname]
        # Legend names
        if pname in names.keys(): leg_name = names[pname]
        else: leg_name = pname
        # If bkg, set fill color and add to stack
        if pname in bkgs.keys():
            h.SetFillColorAlpha(colors[pname],0.2)
            h.SetLineWidth(0) 
            if stackBkg: bkgStack.Add(h)
            if colors[pname] not in colors_in_legend:
                legend.AddEntry(h,leg_name,'f')
                colors_in_legend.append(colors[pname])
                
        # If signal, set line color
        else:
            h.SetLineColor(colors[pname])
            h.SetLineWidth(2)
            if colors[pname] not in colors_in_legend:
                legend.AddEntry(h,leg_name,'l')
                colors_in_legend.append(colors[pname])

    if stackBkg:
        maximum =  bkgStack.GetMaximum()*1.8
        bkgStack.SetMaximum(maximum)
    else:
        maximum = bkgs.values()[0].GetMaximum()*2
        for p in procs.values():
            p.SetMaximum(maximum)
    

    c.cd()
    if len(bkgs.keys()) > 0:
        if stackBkg:
            bkgStack.Draw('hist')
            bkgStack.GetXaxis().SetTitleOffset(1.1)
            bkgStack.Draw('hist')
        else:
            for bkg in bkgs.values():
                bkg.GetXaxis().SetTitleOffset(1.1)
                bkg.Draw('same hist')
    for h in signals.values():
        h.Draw('same hist')
    legend.Draw()

    c.SetBottomMargin(0.12)
    c.SetTopMargin(0.08)
    c.SetRightMargin(0.11)
    CMS_lumi.writeExtraText = 1
    CMS_lumi.extraText = "Preliminary simulation"
    CMS_lumi.lumi_sqrtS = "13 TeV"
    CMS_lumi.cmsTextSize = 0.6
    CMS_lumi.CMS_lumi(c, year, 11)

    c.Print(outfilename,'png')