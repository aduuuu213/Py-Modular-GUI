import random
import time
import traceback

from PySide2.QtCore import QMetaObject, Qt
from PySide2.QtGui import QColor, QPalette
from PySide2.QtWidgets import QLabel, QLineEdit
from utils.logger_manager import logger_manager
from .tool import eptrade


# class PluginOneWorker(QThread):
#     finished = Signal()  # 用于发射任务完成信号
#     progress = Signal(str)  # 用于更新进度信息
    
#     def __init__(self):
#         super().__init__()
#         self._running = False  # 线程运行标志
#         self.logger = logger_manager.logger

#     def run(self):
#         while self._running:
#             # 模拟耗时操作
#             self.logger.info("开始任务")
#             time.sleep(1)  # 每秒执行一次
#             self.progress.emit("Working...")  # 更新进度
#         self.logger.info("任务完成")
#         self.finished.emit()  # 任务完成后发出信号

#     def stop(self):
#         self._running = False  # 停止线程

def main_process(window):
    global OBJ
    logger = logger_manager.logger
    delay_min = window.findChild(QLineEdit, "delay_min")
    delay_max = window.findChild(QLineEdit, "delay_max")
    if delay_min and delay_max:
        delay_min = int(delay_min.text().strip()) if delay_min.text().strip() else 10
        delay_max = int(delay_max.text().strip()) if delay_max.text().strip() else 15
    if delay_min > delay_max:
        delay_min, delay_max = delay_max, delay_min
    logger.info(f"延迟范围: {delay_min} 秒 - {delay_max} 秒")
    while not window.stop_event.is_set():  # 检查是否需要停止
        try:
            for row in range(window.GRID_SIZE[0]):
                for col in range(window.GRID_SIZE[1]):
                    if window.stop_event.is_set():
                        return
                    label = window.findChild(QLabel, f"label_{row}_{col}")
                    if label and label.palette().color(QPalette.Window) == QColor("red"):
                        line_edit = window.findChild(QLineEdit, f"line_edit_{row}_{col}")
                        if line_edit and line_edit.text().strip():
                            # 批量处理申请
                            logger.debug(f"找到红色标签: label_{row}_{col}")
                            try:
                                status = handle_apply(line_edit.text().strip())
                            except Exception as e:
                                if e == '访问出错':
                                    logger.error('访问出错, 自动初始化')
                                    r = login_by_token(window.findChild(QLineEdit, "token").text().strip())
                                    if r:
                                        logger.info('初始化成功')
                                    else:
                                        logger.error('初始化失败')
                                        return
                            color = "#4CAF50" if status else "#FF0000"
                            label.setStyleSheet(f"background-color: {color};")
                            # 随机延迟
                            delay = random.randint(delay_min, delay_max)
                            logger.info(f"等待 {delay} 秒")
                            for i in range(delay):
                                if window.stop_event.is_set():
                                    return
                                time.sleep(1)
                time.sleep(1)
            time.sleep(1)
        except NameError as e:
            logger.error('请先初始化')
            # window.is_running = False
            return


def login_by_token(token):
    global OBJ, logger
    logger = logger_manager.logger
    OBJ = eptrade("username", "password", logger)
    return OBJ.login_by_token(token)

def create_apply_text(window):
    bookingno = window.bill_id.text()
    ctnr_count= window.ctnr_count.text()
    ctnr_type = window.ctnr_type.currentText()
    region = window.region.currentText()
    if not bookingno or not ctnr_count or not ctnr_type:
        window.show_message("错误", "请填写生成信息")
        return 
    # 访问UI元素的示例
    # logger.info(bookingno)
    try:
        r = OBJ.validateBeforeOperate(bookingno)
        logger.debug(r)
        if r:
            try:
                bill_info = OBJ._operate(bookingno)
                logger.debug(bill_info)
                # 获取推荐堆场
                rcmd_yard = OBJ._get_rcmd_yard(bill_info["bill"]["id"], ctnr_type, ctnr_count)
                logger.debug(rcmd_yard)
                # 生成文本
                select_text_all = []
                for item in rcmd_yard["handTypes"]:
                    select_text_all.append(item["relCode"])
                r = window.show_selection_dialog(select_text_all)
                logger.debug('选中的 {}'.format(r))
                if r != -1: 
                    handId = rcmd_yard["handTypes"][r]["id"]
                else:
                    handId = 0
                line_input = window.find_QLineEdit()
                line_input.setText("{}-{}-{}-{}-{}-{}".format(bookingno, bill_info["bill"]["id"], ctnr_count, ctnr_type, region, handId))
                return "有效"
            except BaseException as e:
                traceback.print_exc()
                logger.info("无效 提单号不存在")
                return "无效"
        logger.info("无效 订舱号")
        return "无效 订舱号"
    except BaseException as e:
        logger.error(traceback.format_exc())
        return f"服务故障 {str(e)}"


def handle_apply(text):
    logger = logger_manager.logger
    logger.info("处理申请 {}".format(text))
    parts = text.split('-')
    if len(parts) < 6:
        logger.error("分割后的字符串部分不足6个")
        return "无效输入"
    bookingno, bill_id, ctnr_count, ctnr_type, region, handId = parts
    logger.debug(f"分割结果: 订舱号={bookingno}, 提单号={bill_id}, 集装箱数量={ctnr_count}, 集装箱类型={ctnr_type}, 区域={region}, 手动ID={handId}")
    
    try:
        # 先判断是否可以申请
        msg = OBJ.testfindSuccessfulAppliedCtnrs(bill_id)
        if '未申请箱子' in msg:
            status, msg = OBJ.smlCarrierApplyCtnr(bill_id, ctnr_count, ctnr_type, int(handId), region)
            logger.info("申请结果：{}".format(msg))
            return status
        else:
            logger.info("申请结果：{}".format(msg))
            return True
    except NameError as e:
        logger.info(f"申请结果：未服务初始化")
        return False
    except Exception as e:
        logger.info(f"申请结果：{str(e)}")
        return False
    except BaseException as e:
        logger.error(traceback.format_exc())
        return False