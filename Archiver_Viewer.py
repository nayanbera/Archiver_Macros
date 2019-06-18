import urllib3
import json
import pylab as pl
import datetime
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import QTime, QDate, Qt
import sys
from ReadPVList import ReadPVList
import time
import os


class Archiver_Viewer(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi('Archiver_Viewer.ui',self)
        self.setWindowTitle('Archiver Viewer')
        self.toTime=QTime()
        self.toDate=QDate()
        self.currentTime=self.toTime.currentTime()
        self.currentDate=self.toDate.currentDate()
        self.toDateTimeEdit.setTime(self.currentTime)
        self.toDateTimeEdit.setDate(self.currentDate)
        self.fromDateTimeEdit.setDate(self.currentDate)
        self.fromTime=self.currentTime.addSecs(-3600)
        self.fromDateTimeEdit.setTime(self.fromTime)
        fname='archiver_PVs.txt'
        self.readPV=ReadPVList(fname=fname)
        self.pvList=self.readPV.pvList
        self.checkMotor=self.readPV.checkMotor
        self.update_pvTree()
        self.init_signals()

    def init_signals(self):
        self.fetchDataPushButton.clicked.connect(self.fetchData)
        self.exportDataPushButton.clicked.connect(self.exportData)


    def update_pvTree(self):
        self.pvTreeWidget.clear()
        for category in self.pvList.keys():
            categ=QTreeWidgetItem([category])
            for pv in self.pvList[category].keys():
                if self.checkMotor[pv]:
                    mot=QTreeWidgetItem([pv])
                    for motorPV in self.pvList[category][pv].keys():
                        motPV=QTreeWidgetItem([motorPV, self.pvList[category][pv][motorPV]])
                        mot.addChild(motPV)
                    categ.addChild(mot)
                else:
                    apv=QTreeWidgetItem([pv,self.pvList[category][pv]])
                    categ.addChild(apv)
            self.pvTreeWidget.setColumnCount(3)
            self.pvTreeWidget.addTopLevelItem(categ)
        self.pvTreeWidget.header().setSectionResizeMode(QHeaderView.ResizeToContents)


    def fetchData(self):
        fr=self.fromDateTimeEdit.dateTime().toUTC().toString(Qt.ISODate)
        to=self.toDateTimeEdit.dateTime().toUTC().toString(Qt.ISODate)
        self.unit={}
        self.xraw={}
        self.x={}
        self.y={}
        prg_dlg=QProgressDialog(self)
        prg_dlg.setAutoClose(True)
        items=self.pvTreeWidget.selectedItems()
        prg_dlg.setMaximum(len(items))
        prg_dlg.setMinimum(0)
        prg_dlg.show()
        self.datafull={}
        for i, item in enumerate(items):
            pv=item.text(1)
            # url='http://164.54.162.104:17668/retrieval/data/getData.json?pv=15ID:BLEPS:TEMP1_CURRENT&from=2019-06-17T13:20:00%%C2%B10700&to=2019-06-17T14:20:00%%C2%B10700'
            url = 'http://164.54.162.104:17668/retrieval/data/getData.json?pv=%s&from=%s&to=%s' % (pv, fr, to)
            http = urllib3.PoolManager()
            r = http.request('GET', url)
            # try:
            data = json.loads(r.data)
            self.unit[pv] = data[0]['meta']['EGU']
            self.xraw[pv]=pl.array([item['secs'] for item in data[0]['data']])
            self.x[pv] = pl.array([datetime.datetime.fromtimestamp(item['secs']) for item in data[0]['data']],dtype='datetime64')
            self.y[pv] = pl.array([item['val'] for item in data[0]['data']])
            self.datafull[pv]=pl.vstack((self.xraw[pv],self.y[pv]))
            # except:
            #     QMessageBox.warning(self,'Fetch Error','The data from %s cannot be obtained from the server'%pv,QMessageBox.Ok)
            prg_dlg.setValue(i + 1)
        if bool(self.unit):
            self.updatePlot()

    def updatePlot(self):
        try:
            self.axes2.remove()
        except:
            pass
        if len(self.unit.keys())!=2:
            axis_color='k'
            self.mplWidget.canvas.axes.clear()
            self.mplWidget.canvas.axes.set_xlabel('Time')
            last = None
            ylabel = ''
            for pv in self.unit.keys():
                if self.unit[pv]!=last:
                    ylabel+='%s '%self.unit[pv]
                self.mplWidget.canvas.axes.step(self.x[pv], self.y[pv],label=pv)
                last=self.unit[pv]
            self.mplWidget.canvas.axes.tick_params(axis='y', labelcolor=axis_color)
            self.mplWidget.canvas.axes.set_ylabel(ylabel,color=axis_color)
            leg=self.mplWidget.canvas.axes.legend(loc='best')
            self.mplWidget.canvas.draw()
        else:
            self.mplWidget.canvas.axes.clear()
            pv=list(self.unit.keys())
            color = 'tab:red'
            self.mplWidget.canvas.axes.set_ylabel(pv[0]+'[%s]'%self.unit[pv[0]],color=color)
            self.mplWidget.canvas.axes.step(self.x[pv[0]], self.y[pv[0]],color=color,label=pv)
            self.mplWidget.canvas.axes.tick_params(axis='y',labelcolor=color)
            try:
                self.axes2.clear()
            except:
                self.axes2=self.mplWidget.canvas.axes.twinx()
            color = 'tab:blue'
            self.axes2.set_ylabel(pv[1]+'[%s]'%self.unit[pv[1]], color=color)
            self.axes2.step(self.x[pv[1]], self.y[pv[1]],color=color, label=pv)
            self.axes2.tick_params(axis='y', labelcolor=color)
            self.mplWidget.canvas.draw()
        pl.gcf().autofmt_xdate()

    def exportData(self):
        if bool(self.unit):
            self.dir=QFileDialog.getExistingDirectory(self,'Select a directory to save data')
            for pv in self.unit.keys():
                fheader='Data saved on %s\n'%(time.asctime())
                fheader+='col_names=["time[secs]","pv[%s]"]'%self.unit[pv]
                fname=pv+'_%s.txt'%(time.strftime('%Y%m%d'))
                fname=os.path.join(self.dir,fname.replace(':','_'))
                pl.savetxt(fname,self.datafull[pv],header=fheader,comments='#')
        else:
            QMessageBox.warning(self,'Data Error','No data fetched to save',QMessageBox.Ok)




if __name__=='__main__':
    app = QApplication(sys.argv)
    ex = Archiver_Viewer()
    ex.show()
    sys.exit(app.exec_())
