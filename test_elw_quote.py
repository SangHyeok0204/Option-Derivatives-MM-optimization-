"""
키움 Open API - ELW 실시간 호가 조회 테스트
종목: 52L971 (미래L791삼성전자콜)
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer


class KiwoomAPI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.kiwoom.OnEventConnect.connect(self.on_event_connect)
        self.kiwoom.OnReceiveRealData.connect(self.on_receive_real_data)

        self.login_event_loop = QEventLoop()
        self.connected = False
        self.data_count = 0

    def login(self):
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def on_event_connect(self, err_code):
        """로그인 결과 처리"""
        if err_code == 0:
            print("\n[성공] 로그인 완료")
            self.connected = True

            accounts = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            user_id = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "USER_ID")
            user_name = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "USER_NAME")
            server_type = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")

            print(f"사용자: {user_name} ({user_id})")
            print(f"서버: {'모의투자' if server_type == '1' else '실투자'}")
            print(f"계좌: {accounts}")
        else:
            print(f"\n[실패] 로그인 실패 (에러코드: {err_code})")
            self.connected = False

        self.login_event_loop.exit()

    def set_real_reg(self, screen_no, code_list, fid_list, opt_type):
        """실시간 등록"""
        return self.kiwoom.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            screen_no, code_list, fid_list, opt_type
        )

    def on_receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신"""
        if real_type in ("주식호가잔량", "ELW호가잔량"):
            self.data_count += 1
            print(f"\n{'='*50}")
            print(f"[{self.data_count}] 실시간 호가 수신 - {code} ({real_type})")
            print("=" * 50)

            print("\n[매도호가]")
            for i, fid in enumerate([41, 42, 43, 44, 45], 1):
                price = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, fid).strip()
                qty = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, fid + 20).strip()
                if price:
                    print(f"  {i}차: {price}원 / {qty}주")

            print("\n[매수호가]")
            for i, fid in enumerate([51, 52, 53, 54, 55], 1):
                price = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, fid).strip()
                qty = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, fid + 20).strip()
                if price:
                    print(f"  {i}차: {price}원 / {qty}주")

            if self.data_count >= 10:
                print("\n" + "=" * 50)
                print("[완료] 10개 데이터 수신 완료. 테스트 종료.")
                print("=" * 50)
                self.app.quit()

    def run(self):
        """메인 실행"""
        self.login()

        if not self.connected:
            print("로그인 실패로 종료합니다.")
            return

        print("\n" + "=" * 50)
        print("ELW 실시간 호가 등록 중...")
        print("=" * 50)

        # FID: 41~50 매도호가, 51~60 매수호가, 61~70 매도잔량, 71~80 매수잔량
        fid_list = ";".join([str(i) for i in range(41, 81)])
        result = self.set_real_reg("1000", "52L971", fid_list, "0")
        print(f"실시간 등록 결과: {result}")

        # 5분 타임아웃
        QTimer.singleShot(300000, self.timeout)

        print("\n실시간 데이터 대기 중... (5분 타임아웃)")
        print("호가 변동이 있으면 데이터가 수신됩니다.\n")

        self.app.exec_()

    def timeout(self):
        """타임아웃 처리"""
        if self.data_count == 0:
            print("\n[경고] 대기시간 초과")
            print("장 운영시간이 맞는지, 종목코드가 유효한지 확인해주세요.")
        else:
            print(f"\n[타임아웃] 총 {self.data_count}개 데이터 수신")
        self.app.quit()


if __name__ == "__main__":
    kiwoom = KiwoomAPI()
    kiwoom.run()