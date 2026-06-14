import sys
from PyQt5.QtWidgets import QApplication, QStyleFactory
from gui import BinanceTrader 

if __name__ == '__main__':
    try:
        import requests
        import websockets 
        import pyqtgraph # 참고: pyqtgraph는 이제 차트에 필요없지만, 혹시 모를 다른 용도를 위해 남겨둘 수 있습니다.
        from PyQt5 import QtWebEngineWidgets # ◀◀◀ [추가]
    except ImportError as e:
        print(f"오류: 필요한 라이브러리가 설치되지 않았습니다. ({e})")
        print("터미널에서 'pip install PyQt5 pyqtgraph requests websockets PyQtWebEngine'를 실행하세요.")
        sys.exit(1)

    print("프로그램 시작...")
    
    app = QApplication(sys.argv)
    
    app.setStyle(QStyleFactory.create("Fusion"))
    
    window = BinanceTrader()
    window.show()
    
    sys.exit(app.exec_())