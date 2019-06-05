import os


class ReadPVList(object):
    def __init__(self,fname=None):
        self.motorParams={'User':'RBV','Dial':'DRBV','Offset':'OFF','Direction':'DIR','MotorPos':'RMP',
                          'EncoderPos':'REP',
                          'UseEncoder':'UEIP',
                          'MotorRes':'MRES',
                          'EncoderRes':'ERES'}
        self.data_server='http://chemmat104.cars.aps.anl.gov:17668'
        self.webpath=self.data_server+'/retrieval/ui/'
        self.htmlfolder='/opt/archappl/retrieval/webapps/retrieval/ui/'
        self.href = self.data_server+"/retrieval/ui/viewer/archViewer.html?pv="
        if fname is not None:
            if os.path.exists(fname):
                self.pvList={}
                self.checkMotor={}
                self.pvAll=[]
                self.categories=[]
                self.pvListFileName=fname
                self.parseFile()
        headerfh=open('page-header.txt','r')
        self.headertxt=headerfh.readlines()
        headerfh.close()
        footerfh=open('page-footer.txt','r')
        self.footertxt=footerfh.readlines()
        footerfh.close()



    def parseFile(self):
        fh=open(self.pvListFileName,mode='r')
        lines=fh.readlines()
        for line in lines:
            if line[0]=='#':
                self.categories.append(line[1:].strip())
                self.pvList[self.categories[-1]]={}
            else:
                if line.strip()!='':
                    pvName,val=line.strip().split('=')
                    mot=val.split('(')
                    try:
                        if mot[1][:-1].strip()=='motor':
                            self.checkMotor[pvName.strip()]=True
                    except:
                        self.checkMotor[pvName.strip()]=False
                    if self.checkMotor[pvName.strip()]:
                        self.pvList[self.categories[-1]][pvName.strip()]={}
                        for key in self.motorParams.keys():
                            self.pvList[self.categories[-1]][pvName.strip()][key]=mot[0].strip()+'.'+self.motorParams[key]
                            self.pvAll.append(mot[0].strip()+'.'+self.motorParams[key])
                    else:
                        self.pvList[self.categories[-1]][pvName.strip()]=mot[0].strip()
                        self.pvAll.append(mot[0].strip())
            self.pvNum=len(self.pvAll)

    def create_htmls(self):
        sidebartxt = '<!-- Sidebar -->\n<div class="w3-sidebar w3-light-grey w3-bar-block" style="width:20%">\n <h2 ' \
                     'class="w3-bar-item">Devices</h2>\n'
        for category in sorted(self.pvList.keys()): #For creating sidebar
            sidebartxt += ' <a href="%s%s.html" class="w3-bar-item w3-button">%s</a>\n' % (self.webpath,category,category)
        sidebartxt +='</div>\n\n'

        fh2 = open(self.htmlfolder + 'index.html', 'w')
        fh2.writelines(self.headertxt)
        fh2.writelines(sidebartxt)
        fh2.write('\n<!-- Page Content -->\n')
        fh2.writelines('<div style="margin-left:20%">\n<div class="w3-container w3-teal">\n<h1>ChemMatCARS '
                       'Archiver Appliance</h1></div>\n<div class="w3-container">\n\n')
        fh2.write('<h2>Welcome to ChemMatCARS Archiver</h2>\n')
        fh2.write('<p>Please click on the sidebar items to look into the archived PVs. In order to '
                      'add/remove/update any PVs please contact Mrinal Bera.</p>\n')
        fh2.write('\n')
        fh2.writelines(self.footertxt)
        fh2.close()

        for category in sorted(self.pvList.keys()):
            fh=open(self.htmlfolder+category+'.html','w')

            fh.writelines(self.headertxt)
            fh.writelines(sidebartxt)
            fh.write('\n<!-- Page Content -->\n')
            fh.writelines('<div style="margin-left:20%">\n<div class="w3-container w3-teal">\n<h1>ChemMatCARS '
                          'Archiver Appliance: '+category+'</h1></div>\n<div class="w3-container">\n\n')
            fh.write('\n')

            motortxt = '<h3>Archived Motor PVs</h3>\n'
            motortxt +='<table cellspacing = 10>\n'
            pvtxt = '<h3>Archived PVs</h3>\n'
            pvtxt += '<table cellspacing = 10>\n'
            allotxt=''
            onum=0
            mnum=0
            otherPV=False
            motorPV=False
            for pv in sorted(self.pvList[category].keys()):
                if not self.checkMotor[pv]: #For PVs other than motors
                    otherPV=True
                    pvtxt += '<tr>\n'
                    allotxt+=self.pvList[category][pv]+'&pv='
                    pvtxt+='<td><a href="'+self.href+self.pvList[category][pv]+'">'+pv+'</a></td>\n'
                    pvtxt += '</tr>\n\n'
                    onum+=1
                else:
                    motorPV=True
                    motortxt += '<tr>\n'
                    motortxt += '<td>'+pv+'</td>\n'
                    alltxt=''
                    for key in sorted(self.motorParams.keys()):
                        alltxt+=self.pvList[category][pv][key]+'&pv='
                        motortxt+='<td><a href="'+self.href+self.pvList[category][pv][key]+'">'+key+'</a></td>\n'
                    motortxt += '<td><a href="' + self.href +alltxt[:-4]+ '">All</a></td>\n'
                    motortxt+='</tr>\n\n'
                    mnum+=1
            if mnum>0:
                motortxt+='<tr>\n'
                motortxt+='<td>All</td>\n'
                for key in sorted(self.motorParams.keys()):
                    allsame=''
                    for pv in sorted(self.pvList[category].keys()):
                        if self.checkMotor[pv]:
                            allsame+=self.pvList[category][pv][key]+'&pv='
                    if allsame!='':
                    	motortxt+='<td><a href="'+self.href+allsame[:-4]+'">All</a></td>\n'
                motortxt+='</tr>\n\n'
            if onum>0:
            	pvtxt+='<td><a href="'+self.href+allotxt[:-4]+'">All</a></td>\n'
            motortxt+='</table>\n'
            if motorPV:
                fh.write(motortxt)
            fh.write('\n')
            if otherPV:
                fh.write(pvtxt)
            fh.writelines(self.footertxt)
            fh.close()

            #print('Created %s.html'%category)



if __name__=="__main__":
    ReadPV=ReadPVList(fname='archiver_PVs.txt')
    fh=open('generated_pvList.txt','w')
    for item in ReadPV.pvAll:
        fh.write(item+'\n')
    fh.close()
    ReadPV.create_htmls()


