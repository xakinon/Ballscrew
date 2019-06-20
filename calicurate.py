# -*- coding: utf-8 -*-
import itertools
import math

class Calicurate():
    def __init__(self, calculationConditions, ballscrews=[None], servomotors=[None], couplings=[None], supportunits=[None], linearguides=[None]):
        self.conditions = calculationConditions
        self.ballscrews = ballscrews
        self.servomotors = servomotors
        self.couplings = couplings
        self.supportunits = supportunits
        self.linearguides = linearguides
        self.dicts = []
        self.columns = []

    def commit(self):
        flag = False
        self.dicts = []

        # ストロークでボールねじを選定
        ballscrews = self.choseBallscrewByStroke(self.ballscrews)

        #lists = list( itertools.product(ballscrews, self.servomotors, self.couplings, self.supportunits, self.linearguides) )
        #for ballscrew, servomotor, coupling, supportunit, linearguide in lists:
        for ballscrew, servomotor, coupling, supportunit, linearguide in itertools.product(
            ballscrews, self.servomotors, self.couplings, self.supportunits, self.linearguides):

            calculatedValues = {'ユニット全長':0.0}

            ########### ボールねじの検討 ###########

            # ストロークが条件を満たさなければスキップ
            if self.conditions['ストローク'] > ballscrew['ストローク']:
                if flag:
                    continue

            # 軸方向最大荷重がボールねじの座屈荷重以上ならスキップ
            ballscrew['取付間距離'] = ballscrew['ストローク']
            ballscrew['座屈荷重'] = self.bucklingLoad(ballscrew)
            calculatedValues['軸方向最大荷重'] = self.axialLoad()
            if calculatedValues['軸方向最大荷重'] > ballscrew['座屈荷重']:
                if flag:
                    continue

            # 軸方向最大荷重がボールねじの降伏荷重以上ならスキップ
            ballscrew['降伏荷重'] = 1.15 * (ballscrew['ねじ谷径']**2.0) * (10.0**2.0)
            if calculatedValues['軸方向最大荷重'] > ballscrew['降伏荷重']:
                if flag:
                    continue
            
            # 軸方向最大荷重がボール溝部の静最大許容荷重以上ならスキップ
            ballscrew['静的安全係数'] = 2.0
            ballscrew['静最大許容荷重'] = ballscrew['基本静定格荷重'] / ballscrew['静的安全係数']
            if calculatedValues['軸方向最大荷重'] > ballscrew['静最大許容荷重']:
                if flag:
                    continue

            # 最高回転数がボールねじの危険速度以上ならスキップ
            calculatedValues['最高回転数'] = self.conditions['最高速度'] * 1000.0 / ballscrew['リード'] * 60.0
            ballscrew['危険速度'] = self.criticalSpeed(ballscrew)
            if calculatedValues['最高回転数'] > ballscrew['危険速度']:
                if flag:
                    continue

            # 最高回転数がボールねじの許容回転数(nd値)以上ならスキップ
            if calculatedValues['最高回転数'] > ballscrew['許容回転数']:
                if flag:
                    continue

            # 疲れ寿命
            ballscrew['軸方向平均荷重'] = 120.0
            ballscrew['荷重係数'] = 1.5
            ballscrew['疲れ寿命回転数'] = ( ( ballscrew['基本動定格荷重'] / (ballscrew['軸方向平均荷重']*ballscrew['荷重係数']) )**3.0 ) * (10.0**6.0)

            ########### モーターの検討 ###########

            # 角加速度
            calculatedValues['角加速度'] = 2 * math.pi * self.conditions['最高加速度'] * 1000 / ballscrew['リード']

            # 直線運動体のイナーシャ
            calculatedValues['ワークイナーシャ'] = self.conditions['ワーク質量'] * ( ballscrew['リード']*10**(-3) / (2.0*math.pi) )**2.0

            # イナーシャ比 = モーター以外のイナーシャ合計 / モーターのイナーシャ
            ballscrew['軸慣性モーメント'] = self.shaftInertia(ballscrew)
            calculatedValues['イナーシャ比'] = ( ballscrew['軸慣性モーメント'] + calculatedValues['ワークイナーシャ'] + coupling['イナーシャ'] ) / servomotor['イナーシャ']

            # トルク = イナーシャ合計 * 角加速度
            calculatedValues['最大トルク'] = ( ballscrew['軸慣性モーメント'] + calculatedValues['ワークイナーシャ'] + coupling['イナーシャ'] + servomotor['イナーシャ'] ) * calculatedValues['角加速度']

            # イナーシャ比がモーターの許容イナーシャ比以上ならスキップ
            if calculatedValues['イナーシャ比'] > servomotor['許容イナーシャ比']:
                if flag:
                    continue
            
            # トルクがモーターの最大トルク以上ならスキップ
            if calculatedValues['最大トルク'] > servomotor['最大トルク']:
                if flag:
                    continue
            
            # 最高回転数がモーターの最高回転数以上ならスキップ
            if calculatedValues['最高回転数'] > servomotor['最大回転数']:
                if flag:
                    continue

            ########### カップリングの検討 ###########

            # ボールねじシャンク径がカップリングの穴径の最小以下もしくは最大以上ならスキップ
            if ballscrew['シャンク径'] < coupling['最小穴径'] or ballscrew['シャンク径'] > coupling['最大穴径']:
                if flag:
                    continue
            
            # モーター軸径がカップリングの穴径の最小以下もしくは最大以上ならスキップ
            if servomotor['軸径'] < coupling['最小穴径'] or servomotor['軸径'] > coupling['最大穴径']:
                if flag:
                    continue
            
            # トルクがカップリングの最大トルク以上ならスキップ
            if calculatedValues['最大トルク'] > coupling['最大トルク']:
                if flag:
                    continue

            # 最高回転数がカップリングの最高回転数以上ならスキップ
            if calculatedValues['最高回転数'] > coupling['最大回転数']:
                if flag:
                    continue

            # 各辞書を連結してリストに追加
            calculatedValues['ユニット全長'] = servomotor['全長'] + ballscrew['全長'] + 1
            self.dicts.append(
                self.dictJoint([
                    calculatedValues, 
                    self.replaceKeyDict(ballscrew, 'BS'), 
                    self.replaceKeyDict(servomotor, 'SM'), 
                    self.replaceKeyDict(coupling, 'CP'), 
                    self.replaceKeyDict(supportunit, 'SU'), 
                    self.replaceKeyDict(linearguide, 'LG')
                ])
            )
        
        # モデル用の列リストを作成
        self.columns = ['BSメーカー','BS型番','BSねじ径','BSリード','BSストローク','BS全長','SMメーカー','SM定格出力','SM型番','CPメーカー','CP型番','CP直径','CP全長']
        
        for key in self.dicts[0]:
            if not key in list(self.columns):
                self.columns.append(key)
        
    def dictJoint(self, dicts):
        return_dict_ = {}
        for dict_ in dicts:
            return_dict_.update(dict_)
        return return_dict_

    def replaceKeyDict(self, dict_, str):
        if dict_ is None:
            return {}
        return { str + key:dict_[key] for key in dict_ }

    def axialLoad(self, gravity=9.807, friction_coefficient=0.003):
        mass = self.conditions['ワーク質量']
        acceleration = self.conditions['最高加速度']
        external_force = friction_coefficient * mass * gravity # リニアガイドの摩擦抵抗
        friction_resistance = friction_coefficient * mass * gravity # ボールねじの摩擦抵抗
        inertual_force = mass * acceleration

        going_acceleration  =        friction_resistance + external_force + inertual_force
        going_constant      =        friction_resistance + external_force
        going_deceleration  =        friction_resistance - external_force - inertual_force
        return_acceleration = -1.0 * friction_resistance - external_force - inertual_force
        return_constant     = -1.0 * friction_resistance - external_force
        return_deceleration = -1.0 * friction_resistance + external_force + inertual_force

        load_list = [going_acceleration,  going_constant,  going_deceleration, return_acceleration, return_constant, return_deceleration]
        absolute_load_list = [ abs(x) for x in load_list ]
        
        return max(absolute_load_list)
    
    def bucklingLoad(self, ballscrew):
        # 座屈荷重 [N]
        condition = (self.conditions['支持条件入力側'], self.conditions['支持条件ナット部'])
        #               固定-固定     固定-支持    固定-自由     支持-支持
        coefficient = {(0, 0):19.9, (0, 1):10.0, (0, 2): 1.2, (1, 1): 5.0}
        if not condition in coefficient:
            return -1.0
        return coefficient[condition] * (ballscrew['ねじ谷径']**4.0) / (ballscrew['取付間距離']**2.0) * (10.0**4.0)

    def criticalSpeed(self, ballscrew):
        # 危険速度 [rpm]
        condition = (self.conditions['支持条件ナット部'], self.conditions['支持条件反対側'])
        #               固定-固定     固定-支持     固定-自由    支持-支持
        coefficient = {(0, 0):21.9, (0, 1):15.1, (0, 2): 3.4, (1, 1): 9.7}
        if not condition in coefficient:
            return -1.0
        return coefficient[condition] * ballscrew['ねじ谷径'] / (ballscrew['取付間距離']**2.0) * (10.0**7.0)

    def shaftInertia(self, ballscrew):
        # ねじ軸慣性モーメント [kg*m**2]
        length = ballscrew['全長'] / 10.0 # [cm]
        diameter = ballscrew['ねじ径'] / 10.0 # [cm]
        density = 7.8 * 10.0**(-3) # [kg*cm^3]
        return math.pi * density * length * diameter**4.0 / 32.0 * 10.0**(-4.0)

    def choseBallscrewByStroke(self, ballscrews):

        # ストローク条件以上のボールねじを取得
        ballscrews1 = [ ballscrew for ballscrew in ballscrews if self.conditions['ストローク'] <= ballscrew['ストローク'] ]


        # 辞書に含まれるkeysの要素をそれぞれ結合して文字列として返す
        def judgeString(dict_, keys):
            return ','.join([ str(dict_[key]) for key in dict_ if key in keys ])
        
        # 辞書のリストをキーのリストの要素の組み合わせで分割
        def splitDictsByKeys(dicts, keys):
            strings = list({ judgeString(dict_, keys) for dict_ in dicts })
            dictsByStrings = { string:[] for string in strings }
            for dict_ in dicts:
                dictsByStrings[judgeString(dict_, keys)].append(dict_)
            return dictsByStrings

        # ボールねじを条件ごとに分割
        ballscrewsByStrings = splitDictsByKeys(ballscrews, ['メーカー', 'シリーズ名', 'モデル', 'ねじ径', 'リード'])

        # 分割したリストごとに指定ストロークのボールねじを取得
        ballscrews2 = []
        for key in ballscrewsByStrings:
            splitedBallscrews = ballscrewsByStrings[key]

            # ストロークでソート
            splitedBallscrews.sort(key=lambda x: x['ストローク'])

            # ボールねじリストのストロークがストローク条件を超えたらその前後のボールねじ2本を取得
            strokedBallscrews = []
            for i in range(len(splitedBallscrews)):
                if splitedBallscrews[i]['ストローク'] > self.conditions['ストローク']:
                    strokedBallscrews = [ splitedBallscrews[i-1], splitedBallscrews[i] ]
                    break
            else:
                # breakしなかったらスキップ(=ストローク条件を満たすボールねじが見つからなかったら)
                continue
            
            # 取得した2本のボールねじから指定ストロークのボールねじを作成
            calicurationBallscrew = {}

            # ボールねじの延長量
            addLength = self.conditions['ストローク'] - strokedBallscrews[0]['ストローク']

            # 計算値を使用するキー
            calicurationBallscrewKeys1 = ['ストローク','全長']
            calicurationBallscrewKeys2 = ['許容回転数']

            # 短いボールねじから値をセット
            for key in strokedBallscrews[0]:
                if not key in calicurationBallscrewKeys1 + calicurationBallscrewKeys2:
                    calicurationBallscrew[key] = strokedBallscrews[0][key]


            # 短いボールねじに延長量を足した値をセット
            for key in calicurationBallscrewKeys1:
                calicurationBallscrew[key] = strokedBallscrews[0][key] + addLength
            
            # 短いボールねじに延長量を足した値をセット
            ratio = addLength / (strokedBallscrews[1]['ストローク'] - strokedBallscrews[0]['ストローク'])
            for key in calicurationBallscrewKeys2:
                calicurationBallscrew[key] = strokedBallscrews[0][key] + (strokedBallscrews[1][key] - strokedBallscrews[0][key]) * ratio

            ballscrews2.append(calicurationBallscrew)
        
        return ballscrews1 + ballscrews2
