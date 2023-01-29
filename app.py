# coding: utf -8
import PySimpleGUI as sg  # ライブラリの読み込み
import re

# テーマの設定
sg.theme("Dark Blue 3 ")

# ドメイン設定
L1 = [
    # エンディアン変換
    [sg.Text("・エンディアン変換 ", size=(20, 1)),
     sg.OptionMenu(["変換なし", "変換あり"],
                   background_color="#ffffff",
                   default_value="変換なし",
                   size=(10, 1),
                   key="-ENDIAN-")],
    # 開始アドレス
    [sg.Text("・開始アドレス ", size=(20, 1)),
     sg.InputText(default_text="00000000",
                  text_color="#000000",
                  background_color="#ffffff",
                  key="-ADDRESS-",
                  size=(15, 1))],
    # データ
    [sg.Text("・書き込みデータ", size=(40, 1))],
    [sg.Multiline(text_color="#000000",
                  background_color="#ffffff",
                  size=(100, 10),
                  key="-INPUT_TXT-")],
    # Intel HEXフォーマット
    [sg.Text("・Intel HEXフォーマット", size=(40, 1))],
    [sg.Multiline(text_color="#000000",
                  background_color="#ffffff",
                  size=(100, 10),
                  key="-HEX_TXT-")],
    [sg.Button("実行", border_width=4, size=(15, 1), key="start")]]
# ウィンドウ作成
window = sg.Window("Intel HEX_TOOL ", L1)


def main():
    # イベントループ
    while True:
        # イベントの読み取り（イベント待ち）
        event, values = window.read()
        if event == "start":
            # 不要要素の削除
            input_txt = re.sub('[^0123456789abcdefABCDEF]',
                               '', values["-INPUT_TXT-"])
            # サイズチェック
            if 8 == len(values["-ADDRESS-"]):
                if 0 == (len(input_txt) % 8):
                    output_txt = make_record_fnc(values["-ENDIAN-"], values["-ADDRESS-"], input_txt)
                    window["-HEX_TXT-"].Update(output_txt)
                else:
                    sg.popup_error('書き込みデータは4byte単位で入力してください',title = "入力値不正")
                    pass
            else:
                sg.popup_error('アドレスは4byte単位で入力してください',title = "入力値不正")
                pass
        # 終了条件（ None: クローズボタン）
        elif event is None:
            break
    # 終了処理
    window.close()


def make_record_fnc(endian,address,data):
    BYTE_DATA = bytes.fromhex(data)
    BYTE_LEN = len(BYTE_DATA)
    TYPE00_MAX_WRITE_DATA = 16
    TYPE00_MAX_LOW = -(-BYTE_LEN // TYPE00_MAX_WRITE_DATA) # 切り上げ
    TYPE04_COUNT = 0
    write_offset = 0
    return_data = ""
    # I32HEXフォーマット作成
    for write_low in range(TYPE00_MAX_LOW):
        write_offset = write_low*TYPE00_MAX_WRITE_DATA
        # レコードタイプ04作成
        if -(-(int("0x"+address[4:],16) + write_offset)//65536) != TYPE04_COUNT or address == "00000000":
            TYPE04_COUNT = -(-(int("0x"+address[4:],16) + write_offset)//65536)
            # チェックサム算出
            type04_addr = int("0x"+address,16) + write_offset
            type04_chk_sum_data = b"\x02" + b"\x00\x00" +  b"\x04" + bytes.fromhex(format(int(type04_addr//65536), '04x'))
            type04_chk_sum = hex(256-sum(type04_chk_sum_data)%256)
            type04_record = ":" + type04_chk_sum_data.hex() + type04_chk_sum[2:].zfill(2)
            return_data += type04_record + "\n"
        # 16byte単位のレコードタイプ00作成
        if 16 <= BYTE_LEN - write_offset:
            type00_addr = int("0x"+address[4:],16) + write_offset
            # エンディアン変換
            if "変換なし" == endian:
                type00_data = BYTE_DATA[write_offset:write_offset+TYPE00_MAX_WRITE_DATA]
            else:
                type00_data = make_chenge_endian(BYTE_DATA[write_offset:write_offset+TYPE00_MAX_WRITE_DATA])
            # チェックサム算出
            type00_chk_sum_data = b"\x10" + bytes.fromhex(format(int(type00_addr%65536), '04x')) + b"\x00" + type00_data
            type00_chk_sum = hex(256-sum(type00_chk_sum_data)%256)
            type00_record = ":" + type00_chk_sum_data.hex() + type00_chk_sum[2:].zfill(2)
            return_data += type00_record + "\n"
            # オフセット更新
            write_offset += TYPE00_MAX_WRITE_DATA
        # 16byte未満のレコードタイプ00作成
        elif 0 < BYTE_LEN - write_offset:
            type00_addr = int("0x"+address[4:],16) + write_offset
            type00_len = len(BYTE_DATA[write_offset:])
            # エンディアン変換
            if "変換なし" == endian:
                type00_data = BYTE_DATA[write_offset:]
            else:
                type00_data = make_chenge_endian(BYTE_DATA[write_offset:])
            # チェックサム算出
            type00_chk_sum_data = type00_len.to_bytes(1,"big") + bytes.fromhex(format(int(type00_addr%65536), '04x')) +  b"\x00" + type00_data
            type00_chk_sum = hex(256-sum(type00_chk_sum_data)%256)
            type00_record = ":" + type00_chk_sum_data.hex() + type00_chk_sum[2:].zfill(2)
            return_data += type00_record + "\n"
            break
        else:
            break
    # レコードタイプ01作成
    return_data += ":00000001FF" + "\n"
    return return_data


def make_chenge_endian(data):
    return_data = bytearray(data)
    for i in range(len(data)):
        return_data[i] = data[(i//4)*4 + (3-i%4)]
    return return_data


if __name__ == '__main__':
    main()
