"""
Arcore
=
version:qwq (2024/8/26)
'
Created by Zaid_J vs. N0N_ame
'
"""


import re

def AFFStatement2AFFObject(AFFStatement):
    """
    将aff文件语句转为可处理对象。
    
    参数:
        timinggroup: 时间组。
        note: 地面单点音符
        hold: 地面长按音符
        arc: 音弧
        timing: 时间语句
        scenecontrol: 场景控制语句
        camera: 镜头语句
    """
    if "timinggroup" in AFFStatement: return 1
    elif "}" in AFFStatement: return 0
    elif AFFStatement == "": return None
    elif AFFStatement[0] == '(':
        obj = Note()
    elif 'hold' in AFFStatement:
        obj = Hold()
    elif 'arc'  in AFFStatement:
        obj = Arc()
    elif 'timing' in AFFStatement:
        obj = Timing()
    elif 'scenecontrol' in AFFStatement:
        obj = SceneControl()
    elif 'camera' in AFFStatement:
        obj = Camera()

    obj.SetValueFromAFFStatement(AFFStatement)
    return obj

class Chart:
    """
    代表谱面。

    AFF语句格式:
        
        "AudioOffset:"AudioOffset
        "TimingPointDensityFactor:"TimingPointDensityFactor
        -
        defaulttiminggroup
        timinggrouplist

            
    属性:

        AudioOffset: 谱面整体向前(-)/向后(+)移动多少毫秒。
        TimingPointDensityFactor: 音弧和地面长按音符的物量密度调整为正常值的多少倍。
        defaulttiminggroup: 主时间组所有语句。
        timinggrouplist: 所有时间组。


    需要注意:

        1.TimingPointDensityFactor==1时可省略

        2.在"-"所在的行之前，
        可以参照AudioOffset和TimingPointDensityFactor两行的格式写自己的“标注”
        但是并不会有任何效果，物件的读取从"-"所在的行之后开始

        3.每张谱面必须有defaulttiminggroup，
        timinggrouplist可为空。

    方法:
        __init__(self,AudioOffset=0,TimingPointDensityFactor=1.0,defaulttiminggroup=[],timinggrouplist=[]):
            初始化谱面属性。可以通过参数设置属性的初始值。
        
        AddTimingGroup(self,timinggroup):
            添加一个新的时间组。

        AddObject(self,defaulttiminggroupobject):
            添加一个新的主时间组。
        
        ReadFile(self, AFFPath):
            从该路径中读取aff文件。
        
        SaveFile(self,AFFPath):
            将数据保存为该路径下的aff文件。
    """
    def __init__(self,AudioOffset=0,TimingPointDensityFactor=1.0,defaulttiminggroup=[],timinggrouplist=[]):
        """
        初始化谱面。

        参数:

            AudioOffset: 谱面整体向前(-)/向后(+)移动多少毫秒。默认值为0。
            TimingPointDensityFactor: 音弧和地面长按音符的物量密度调整为正常值的多少倍。默认值为1.0。
            defaulttiminggroup: 主时间组所有语句。默认值为空。
            timinggrouplist: 所有时间组。默认值为空。
        """
        self.AudioOffset = AudioOffset
        self.TimingPointDensityFactor=TimingPointDensityFactor
        self.defaulttiminggroup=defaulttiminggroup
        self.timinggrouplist=timinggrouplist
    
    def AddTimingGroup(self,timinggroup):
        """
        添加一个新的时间组。
        
        参数:
            timinggroup: 时间组内包含的语句。
        """
        self.timinggrouplist.append(timinggroup)
    
    def AddObject(self,defaulttiminggroupobject):
        """
        添加一个新的物件。
        
        参数:
            defaulttiminggroupobject: 主时间组内包含的语句。
        """
        self.defaulttiminggroup.append(defaulttiminggroupobject)

    def ReadFile(self, AFFPath):
        """
        读取aff文件。

        参数:

            AFFPath: 读取谱面地址。
        """
        chart_=open(AFFPath,'r')
        chart = chart_.read().split("\n")
        chart_.close()
        nowloc = 0
        for i in range(0,3):
            if chart[i] == "-":
                nowloc = i+1
            for j in range(0,i):
                if "AudioOffset" in chart[j]:
                    self.AudioOffset = (chart[j].split(":")[1])
                if "TimingPointDensityFactor" in chart[j] :
                    self.TimingPointDensityFactor = (chart[j].split(":")[1])

        while nowloc < len(chart):
            obj = AFFStatement2AFFObject(chart[nowloc])
            if obj == 1:
                for j in range(nowloc,len(chart)):
                    if AFFStatement2AFFObject(chart[j]) == 0:
                        timinggroup = TimingGroup()
                        timinggroup.SetValueFromAFFStatement("".join(chart[nowloc:j+1]))
                        self.AddTimingGroup(timinggroup)
                        nowloc = j+1
                        break
            elif obj == None:
                nowloc+=1
            else:
                self.AddObject(obj)
                nowloc+=1
            
            
    def SaveFile(self,AFFPath):
        """
        保存aff文件。

        参数:

            AFFPath: 保存谱面地址。
        """
        chart=open(AFFPath,'w')
        chart.writelines(f"AudioOffset:{self.AudioOffset}\n")
        if not (-0.000000001 < self.TimingPointDensityFactor - 1.0 < 0.000000001):
            chart.writelines(f"TimingPointDensityFactor:{self.TimingPointDensityFactor}\n")
        chart.writelines("-\n")
        for obj in self.defaulttiminggroup:
            chart.writelines(obj.GetAFFStatement()+'\n')
        for timinggroup in self.timinggrouplist:
            chart.writelines(timinggroup.GetAFFStatement()+'\n')
        chart.close()

class TimingGroup:
    """
    代表时间组对象。

    AFF语句格式:
        
        
        timinggroup(attribute){
            timinggroupobject
            };

            
    属性:

        attribute: 时间组特殊效果标识。
        timinggroupobject: 时间组内包含的语句。


    需要注意:

    
        1.每一个时间组物件按照timinggroupobject内部的时间语句运行，
        并且至少包含一个时间语句，因此可以实现同时刻不同note流速。

        2.timinggroupobject中的时间语句不会产生小节线，
        小节线是由所有时间组外面的时间语句(主时间组)决定的。

        3.一张谱面理论可以存在无限多个时间组，
        也可以仅由starttime=0的时间语句和无数时间组组成

        4.可以通过在括号内添加标识来达到特殊效果，不填则不使用任何特殊效果。
        不同特殊效果之间可以叠加，用下划线隔开即可

    目前已有特殊效果标识: 
    
    
            1.noinput: 
            此时本时间组内的物件
            只有显示效果，没有打击效果和物量，不会判定为击中。
            noinput中的音弧和地面长按音符在经过判定线后依然会消失而不会直接穿过
            noinput中的音弧保留了部分判定，因此依然可以实现一些正常的判定特性，
            如当异色音弧相交时，可以用任意一只手去接/换手
            
            2.fadingholds: 
            此时在未击中地面长按音符时，地面长按音符会进行alpha渐变效果，直到变成未击中时的alpha
            此效果仅对该时间组中的地面长按音符生效，其他物件不受影响
            与noinput叠加时会正常触发fadingholds效果（但是你仍然无法击中地面长按音符）

            3.anglex/angley: 
            分别表示对时间组内的天空音符的下落轨迹进行旋转，
            旋转轴为经过天空音符在判定平面落点的平行于x/y轴的直线，
            其后需要接一个非负整数参数，表示旋转角（单位: 度）的10倍
            实际落点和判定位置不受影响
            此特殊效果仅影响天空音符，不影响地面tap/实体Arc/黑线
            x轴旋转时正方向为上转，y轴旋转时正方向为向左转
            两者可以叠加，叠加时先绕x轴平行线转再绕y轴平行线转，不受参数顺序影响

    方法:
        __init__(self,attribute="",timinggroupobjectlist=[]):
            初始化时间组的属性。可以通过参数设置属性的初始值。
        
        AddObject(self,timinggroupobject):
            添加一个新的时间组。
        
        SetValueFromAFFStatement(self, AFFStatement):
            从 AFF 语句中提取属性值并设置时间组的属性。此方法解析给定的时间组，提取其中的属性值，并更新时间组的属性。
        
        GetAFFStatement(self):
            返回时间组的 AFF 语句表示。生成一个字符串，表示时间组的所有属性。
    """
    def __init__(self,attribute="",timinggroupobjectlist=[]):
        """
        初始化时间组实例。

        参数:


            attribute: 时间组特殊效果标识。默认值为空。
            timinggroupobject: 时间组内包含的语句。默认值为空。
        """
        self.attribute = attribute
        self.timinggroupobjectlist = timinggroupobjectlist
    
    def AddObject(self,timinggroupobject):
        """
        添加一个新的物件。
        
        参数:
            timinggroupobject (int): 时间组内包含的语句。
        """
        self.timinggroupobjectlist.append(timinggroupobject)
    
    def SetValueFromAFFStatement(self,AFFStatement):
        """
        从 AFF 语句中提取属性值并设置时间组的属性。
        
        参数:
            AFFStatement (str): 包含时间组属性。
        """
        value = re.findall(r'timinggroup\(([^)]*)\)\{([^}]*)\};?', AFFStatement)[0]
        self.attribute = value[0]
        self.timinggroupobjectlist = [AFFStatement2AFFObject(affstatement) for affstatement in value[1].split(';')[:-1]]

    def GetAFFStatement(self):
        """
        返回时间组对应的 AFF 格式语句。

        返回:
            str: 时间组对应的 AFF 格式语句。
        """
        AFFStatements=[("  "+timinggroupobject.GetAFFStatement()) for timinggroupobject in self.timinggroupobjectlist]
        return f"timinggroup({self.attribute})" + "{\n" + ('\n'.join(AFFStatements)) + "\n};"



class Note:
    """
    代表地面单点音符(Note)对象。

    AFF语句格式:
        (starttime, lane);

    属性:

        starttime (int): 地面Note所在时间，数字为非负整数。
        lane (float/int): 轨道，表示地面单点音符所在的轨道，可以是浮点数或整数。
                          4k整数范围为1~4；6k整数范围为0~5；
                          浮点数轨道坐标与arc坐标的映射公式为 -0.5+lane*2。

    方法:
        __init__(starttime=0, lane=1):
            初始化一个地面单点音符实例。
        
        SetValueFromAFFStatement(AFFStatement):
            从 AFF 语句中提取并设置地面单点音符的属性值。
        
        GetAFFStatement():
            返回地面单点音符对象对应的 AFF 格式语句。
    """
    def __init__(self, starttime=0, lane=1):
        """
        初始化地面单点音符实例。

        参数:
            starttime (int): 地面单点音符开始时间。默认值为 0。
            lane (float/int): 地面单点音符所在的轨道。默认值为 1。
        """
        self.starttime = starttime
        self.lane = lane

    def SetValueFromAFFStatement(self, AFFStatement):
        """
        从 AFF 语句中提取地面单点音符的开始时间和轨道，并更新实例的属性。

        参数:
            AFFStatement (str): 包含地面单点音符信息的 AFF 语句字符串。
        """
        value = re.findall(r'\((\d+),([-]?\d+(\.\d+)?)\);?', AFFStatement)[0]
        self.starttime = value[0]
        self.lane = float(value[1]) if '.' in value[1] else int(value[1])

    def GetAFFStatement(self):
        """
        返回地面单点音符对象对应的 AFF 格式语句。

        返回:
            str: 地面单点音符对象对应的 AFF 格式语句。
        """
        return f"({self.starttime},{self.lane});"

class Hold:
    """
    代表地面长按音符(Hold)对象。

    AFF语句格式:
        (starttime, endtime, lane);

    属性:

        starttime (int): 地面长按音符的开始时间，数字为非负整数。
        endtime (int): 地面长按音符的结束时间，数字为非负整数。
        lane (float/int): 轨道，表示地面单点音符所在的轨道，可以是浮点数或整数。
                          4k整数范围为1~4；6k整数范围为0~5；
                          浮点数轨道坐标与arc坐标的映射公式为 -0.5+lane*2。

    需要注意: 
    
    
            starttime < endtime 

    方法:
        __init__(starttime=0, endtime=1, lane=1):
            初始化地面长按音符实例。
        
        SetValueFromAFFStatement(AFFStatement):
            从 AFF 语句中提取并设置地面长按音符的属性值。
        
        GetAFFStatement():
            返回地面长按音符对象对应的 AFF 语句。
    """
    def __init__(self, starttime=0, endtime=1, lane=1):
        """
        初始化地面长按音符实例。

        参数:
            starttime (int): 地面长按音符的开始时间。默认值为 0。
            endtime (int): 地面长按音符的结束时间。默认值为 1。
            lane (float/int): 地面长按音符所在的轨道。默认值为 1。
        """
        self.starttime = starttime
        self.endtime = endtime
        self.lane = lane

    def SetValueFromAFFStatement(self, AFFStatement):
        """
        从 AFF 语句中提取地面长按音符的开始时间、结束时间和轨道，并更新实例的属性。

        参数:
            AFFStatement (str): 包含地面长按音符信息的 AFF 语句字符串。
        """
        value = re.findall(r'\((\d+),(\d+),([-]?\d+(\.\d+)?)\);?', AFFStatement)[0]
        self.starttime = int(value[0])
        self.endtime = int(value[1])
        self.lane = float(value[2]) if '.' in value[2] else int(value[2])

    def GetAFFStatement(self):
        """
        返回地面长按音符对象对应的 AFF 格式语句。

        返回:
            str: 地面长按音符对象对应的 AFF 格式语句。
        """
        return f"hold({self.starttime},{self.endtime},{self.lane});"

class Arc:
    """
    代表音弧(Arc)对象。

    AFF语句格式:
        arc(starttime,endtime,startx,endx,easing,starty,endy,color,fx,isvoid)[arctap(time1),...,arctap(timex)];

    属性:


        starttime (int): 音弧的开始时间。
        endtime (int): 音弧的结束时间。
        startx (float): 音弧起始点的 X 坐标。
        endx (float): 音弧结束点的 X 坐标。
        easing (str): 缓动类型(可以使用b,s,si,so,sisi,siso,sosi,soso)。
        starty (float): 音弧起始点的 Y 坐标。
        endy (float): 音弧结束点的 Y 坐标。
        color (int): 音弧的颜色值。
        fx (str): 替换Arctap打击音效和模型外观，对整条arc对象上所有的Arctap生效。
                  fx应用举例: 填写glass_wav，将把/(songid)/glass.wav作为打击音效。
        isvoid (bool): 指示音弧是否为黑线。
        arctaplist (list of int): 音弧的附加天空单点音符(Arctap)的时间点。

    需要注意: 


            1.starttime < endtime

            2.若starttime == endtime，则easing、arctaplist、fx无意义。

            3.当color值为3，且starttime == endtime，starty == endy，
            该arc对象会变成横缩放Arctap，作一条以startx为端点，endx为延长点的线段，
            线段长度即为Arctap缩放后的具体长度；
            此时填入fx仍会生效，但是Arctap的大小保持正常形态。

            4.若arc对象包含至少1个以上的arctap，则isvoid参数无意义。

            5.若arc对象没有任何arctap，则fx参数无意义。

            6.fx对象在填写时只能出现英文字母,"_",以及打击音文件类型后缀，
            否则无论该arc对象是否有arctap都会导致游戏崩溃。
                 

    方法:
        __init__(self, starttime=0, endtime=0, startx=0.00, endx=0.00, easing='b', starty=0.00, endy=0.00, color=0, fx="none", isvoid=False, arctaplist=[]):
            初始化 Arc 对象的属性。可以通过参数设置属性的初始值。
        
        AddSkyTap(self, starttime):
            添加天空单点音符。
        
        SetValueFromAFFStatement(self, AFFStatement):
            从 AFF 语句中提取属性值并设置 Arc 对象的属性。此方法解析给定的 AFF 语句，提取其中的属性值，并更新 Arc 对象的属性。
        
        GetAFFStatement(self):
            返回 Arc 对象的 AFF 语句表示。生成一个字符串，表示 Arc 对象的所有属性及其附加天空单点音符时间列表(如果有)。
    """
    def __init__(self, starttime=0,endtime=0,startx=0.00,endx=0.00,easing='b',starty=0.00,endy=0.00,color=0,fx="none",isvoid=False,arctaplist=[]):
        """
        初始化Arc对象实例。

        参数:
            starttime (int): Arc对象的开始时间。默认值为 0。
            endtime (int): Arc对象的结束时间。默认值为 1。
            startx (float): 音弧起始点的 X 坐标。默认值为 0.00。
            endx (float): 音弧结束点的 X 坐标。默认值为 0.00。
            easing (str): 缓动类型。默认值为 b。
            starty (float): 音弧起始点的 Y 坐标。默认值为 0.00。
            endy (float): 音弧结束点的 Y 坐标。默认值为 0.00。
            color (int): 音弧的颜色值。默认值为 0。
            fx (str): 替换Arctap打击音效和模型外观。默认值为 none。
            isvoid (bool): 指示音弧是否为黑线。默认值为 False。
            arctaplist (list of int): 音弧的附加天空单点音符(Arctap)的时间点。
        """
        self.starttime=int(starttime)
        self.endtime=int(endtime)
        self.startx=float(startx)
        self.endx=float(endx)
        self.easing=easing
        self.starty=float(starty)
        self.endy=float(endy)
        self.color=int(color)
        self.fx=fx
        self.isvoid=bool(isvoid)
        self.arctaplist=arctaplist
    
    def AddSkyTap(self,starttime):
        """
        向音弧中添加一个新的天空单点音符。
        
        参数:
            starttime (int): 要添加的天空单点音符时间。
        """
        self.arctaplist.append(starttime)

    def SetValueFromAFFStatement(self, AFFStatement):
        """
        从 AFF 语句中提取属性值并设置 Arc 对象的属性。
        
        参数:
            AFFStatement (str): 包含 Arc 属性值和附加天空单点音符的 AFF 语句。
        """
        value = re.findall(r'arc\((\d+),(\d+),([-]?\d*\.?\d+),([-]?\d*\.?\d+),([^,]+),([-]?\d*\.?\d+),([-]?\d*\.?\d+),(\d+),([^,]+),([^,]+)\)(?:\[(.*?)\])?(?:;)?$', AFFStatement)[0]
        self.starttime          =int(value[0])
        self.endtime            =int(value[1])
        self.startx             =float(value[2])
        self.endx               =float(value[3])
        self.easing             =value[4]
        self.starty             =float(value[5])
        self.endy               =float(value[6])
        self.color              =int(value[7])
        self.fx                 =value[8]
        self.isvoid             =bool(value[9])
        self.arctaplist         =re.findall(r'arctap\((\d+)\),?',value[10])

    def GetAFFStatement(self):
        """
        返回音弧对象对应的 AFF 格式语句。

        返回:
            str: 音弧对象对应的 AFF 格式语句。
        """
        return f"arc({self.starttime},{self.endtime},{self.startx},{self.endx},{self.easing},{self.starty},{self.endy},{self.color},{self.fx},{self.isvoid})" + (('[' + ','.join([f"arctap({starttime})" for starttime in self.arctaplist]) + ']') if len(self.arctaplist) != 0 else "") + ";"
    
class Timing:
    """
    代表时间语句(Timing)对象。

    AFF语句格式:
        timing(starttime, bpm, beat);

    属性:

        starttime (int): 时间语句生效时间，数字为非负整数。
        bpm (float): 节奏速度，数字为小数。
        beat (float): 表示每多少个四分音符(拍)为一小节（出现一条小节线），
                      数字为小数，当bpm不为0时不可为0。

    需要注意: 
    
    
            1.每个谱面/时间组一定要有一个starttime=0的时间语句，
            并且其bpm数值要大于等于0，beats数值不为负数，才可被正常读取。
            2.除了包含在时间组以外的时间语句（主时间组），
            都会在轨道的starttime处生成一条小节线。
            如果时间语句前后时间不超过1ms，则后面的时间语句不生成小节线。

    方法:
        __init__(self, starttime=0, bpm=0.00, beat=4.00):
            初始化时间语句实例。
        
        SetValueFromAFFStatement(AFFStatement):
            从 AFF 语句中提取并设置时间语句的属性值。
        
        GetAFFStatement():
            返回时间语句对象对应的 AFF 语句。
    """
    def __init__(self, starttime=0, bpm=0.00, beat=4.00):
        """
        初始化时间语句实例。

        参数:
            starttime (int): 时间语句的开始时间。默认值为 0。
            bpm (float): 节奏速度。默认值为 0.00。
            beat (float): 每多少个四分音符(拍)为一小节。默认值为 4.00。
        """
        self.starttime = int(starttime)
        self.bpm = float(bpm)
        self.beat = float(beat)

    def SetValueFromAFFStatement(self, AFFStatement):
        """
        从 AFF 语句中提取属性值并设置时间语句的属性。
        
        参数:
            AFFStatement (str): 包含时间语句属性。
        """
        value = re.findall(r'timing\((\d+),([-]?\d*\.?\d+),([\d.]+)\);?', AFFStatement)[0]
        self.starttime = int(value[0])
        self.bpm = float(value[1])
        self.beat = float(value[2])

    def GetAFFStatement(self):
        """
        返回时间语句对应的 AFF 格式语句。

        返回:
            str: 时间语句对应的 AFF 格式语句。
        """
        return f"timing({self.starttime},{self.bpm},{self.beat});"

class SceneControl:
    """
    代表场景控制语句(SceneControl)对象。

    AFF语句格式:
        scenecontrol(starttime, sctype, duration, flag);

    属性:

        starttime (int): 场景控制生效时间，数字为非负整数。
        sctype: 要执行的场景控制类型。
        duration (float): 持续时间。
        flag (float): 参数。

    目前已知可填写的sctype及其参数情况如下: 
    
    
            1.trackhide: 隐藏轨道

            2.trackshow: 显示轨道

            以上两种场景控制语句不填duration和flag。
        
            "scenecontrol(starttime,trackhide/trackshow);"
            等效于没有黑色背景特效的:
            "scenecontrol(starttime,trackdisplay,1.00,0/255);"

            3.trackdisplay: 轨道透明度控制
            duration: 轨道从当前alpha变换到目标alpha(flag)所要花费的时间，
            数字为小数，单位为秒，填0.00等价于填1.00
            flag: 轨道需要变换到的目标alpha值，可以填非负整数；

            小于255时有黑色背景特效，否则没有；
            0为轨道完全透明，255为轨道完全不透明，
            大于等于256时透明度溢出（可看作透明度对256取余数计算）。

            4.redline: 背景红线效果
            duration: 红线存在的时间，数字为小数，单位为秒
            flag: 无意义
            
            5.arcahvdistort: Arcahv解锁演出时的背景变形效果

            6.arcahvdebris: Arcahv解锁演出时的背景碎片效果
            duration: 从当前alpha变换为目标alpha的持续时间，数字为小数，单位为秒
            flag: 目标alpha值
            
            7.hidegroup: 是否隐藏该时间组(timinggroup)内的note
            duration: 无意义
            flag: 1/0->隐藏/显示该时间组的note
            
            8.enwidencamera: 使Camera按一定比例远离轨道，同时skyinput也会变高

            9.enwidenlanes: 使轨道两侧的ExtraLane(0轨和5轨)展示

            两种enwiden类型的scenecontrol的用法如下:
            duration: 持续时长(ms)
            flag: 1/0->淡入/淡出该事件展示的效果
            
            enwidencamera的相机移动效果实际相当于
            camera(starttime,0,450,450,0,0,0,s,duration);，
            但enwidencamera会同时将Sky Input线移动至Arc坐标下y=1.61处，
            同时也不会禁用玩家接触Arc时导致的视角偏移。

    方法:
        __init__(self, starttime, sctype, duration, flag):
            初始化场景控制语句实例。
        
        SetValueFromAFFStatement(AFFStatement):
            从 AFF 语句中提取并设置场景控制语句的属性值。
        
        GetAFFStatement():
            返回场景控制语句对象对应的 AFF 语句。
    """
    def __init__(self, starttime=0, sctype="", duration=0.00, flag=0):
        """
        初始化场景控制语句实例。

        参数:
            starttime (int): 场景控制生效时间。默认值为0。
            sctype: 要执行的场景控制类型。默认值为空。
            duration (float): 持续时间。默认值为0.00。
            flag (float): 参数。默认值为0。
        """
        self.starttime = int(starttime)
        self.sctype = sctype
        self.duration = float(duration)
        self.flag = int(flag)%2

    def SetValueFromAFFStatement(self, AFFStatement):
        """
        从 AFF 语句中提取属性值并设置场景控制语句的属性。
        
        参数:
            AFFStatement (str): 包含场景控制语句属性。
        """
        value = re.findall(r'scenecontrol\((\d+),([^.]+),([\d.]+),(\d+)\);?', AFFStatement)[0]
        self.starttime = int(value[0])
        self.sctype = value[1]
        self.duration = float(value[2])
        self.flag = int(value[3])%2

    def GetAFFStatement(self):
        """
        返回场景控制语句对应的 AFF 格式语句。

        返回:
            str: 场景控制语句对应的 AFF 格式语句。
        """
        return f"scenecontrol({self.starttime},{self.sctype},{self.duration},{self.flag});"

class Camera:
    """
    代表镜头语句(Camera)对象。

    AFF语句格式:
        camera(starttime,positionx,positiony,positionz,rotationx,rotationy,rotationz,easing,duration);

    属性:

    
        以垂直判定面为基准，
        设横向为x轴(左右)
        纵向为y轴(上下)
        沿轨道方向为z轴(远近)
        建立空间直角坐标系
        starttime (int): 镜头语句生效时间，数字为非负整数。
        positionx (px): x轴移动，左负右正
        positiony (px): y轴移动，下负上正
        positionz (px): z轴移动，前负后正
        rotationx (deg°): xoy平面角度，逆时针-正 顺时针-负
        rotationy (deg°): yoz平面角度，抬头-正 低头-负
        rotationz (deg°): xoz平面角度，逆时针-正 顺时针-负
        easing (string): qi、qo、reset、l
        (qi=Cubic in
        qo=Cubic out
        reset=重置Camera状态返回原点
        非上述三个值则均为Linear)
        duration (ms): 语句持续时间

    需要注意: 
    
    
            当easing不为reset时将禁用玩家接触Arc时导致的视角偏移。

    方法:
        __init__(starttime=0, endtime=1, lane=1):
            初始化镜头语句实例。
        
        SetValueFromAFFStatement(AFFStatement):
            从 AFF 语句中提取并设置镜头语句的属性值。
        
        GetAFFStatement():
            返回镜头语句对象对应的 AFF 语句。
    """
    def __init__(self, starttime=0, positionx=0.00, positiony=0.00, positionz=0.00, rotationx=0.00, rotationy=0.00, rotationz=0.00, easing='l', duration=0):
        """
        初始化镜头语句实例。

        参数:
            starttime (int): 镜头语句生效时间。默认值为0。
            positionx (px): x轴移动。默认值为0.00。
            positiony (px): y轴移动。默认值为0.00。
            positionz (px): z轴移动。默认值为0.00。
            rotationx (deg°): xoy平面角度。默认值为0.00。
            rotationy (deg°): yoz平面角度。默认值为0.00。
            rotationz (deg°): xoz平面角度。默认值为0.00。
            easing (string): qi、qo、reset、l。默认值为l。
            duration (ms): 语句持续时间。默认值为0。
        """
        self.starttime = int(starttime)
        self.positionx = float(positionx)
        self.positiony = float(positiony)
        self.positionz = float(positionz)
        self.rotationx = float(rotationx)
        self.rotationy = float(rotationy)
        self.rotationz = float(rotationz)
        self.easing = easing
        self.duration = int(duration)

    def SetValueFromAFFStatement(self, AFFStatement):
        """
        从 AFF 语句中提取属性值并设置镜头语句的属性。
        
        参数:
            AFFStatement (str): 包含镜头语句属性。
        """
        value = re.findall(r'camera\((\d+),([-]?\d*\.?\d+),([-]?\d*\.?\d+),([-]?\d*\.?\d+),([-]?\d*\.?\d+),([-]?\d*\.?\d+),([-]?\d*\.?\d+),([^.]+),(\d+)\);?', AFFStatement)[0]
        self.starttime = int(value[0])
        self.positionx = float(value[1])
        self.positiony = float(value[2])
        self.positionz = float(value[3])
        self.rotationx = float(value[4])
        self.rotationy = float(value[5])
        self.rotationz = float(value[6])
        self.easing = value[7]
        self.duration = int(value[8])

    def GetAFFStatement(self):
        """
        返回镜头语句对应的 AFF 格式语句。

        返回:
            str: 镜头语句对应的 AFF 格式语句。
        """
        return f"camera({self.starttime},{self.positionx},{self.positiony},{self.positionz},{self.rotationx},{self.rotationy},{self.rotationz},{self.easing},{self.duration});"
    
chart = Chart()
chart.ReadFile("3.aff")
chart.SaveFile("1.aff")