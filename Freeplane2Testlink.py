# -*- coding: utf-8 -*-
import logging.config
import os
from xml.etree import ElementTree as ET
from lxml import etree as lxmlET
import sys


def CDATA(text=None):
    element = ET.Element('![CDATA[')
    element.text = text
    return element


def get_freeplanefile(path):
    ''' for windows'''
    L = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if os.path.splitext(file)[1] == '.xml':
                # L.append(os.path.join(root, file))
                L.append(path + '/' + file)
            if os.path.splitext(file)[1] == '.mm':
                # L.append(os.path.join(root, file))
                L.append(path + '/' + file)
        if len(L) == 0:
            logging.error(path + '\nThere is no FreeMind file,Please check out!')
        return L


def _last_tds_node(node):
    if node.attrib.has_key('LINK'):
        return False
    for child in node.findall('node'):
        if not (child.attrib.has_key('LINK')):
            return False
    return True


class FreeMind(object):
    def __init__(self, logger, ):
        self.logger = logger
        self.log_prefix = 'FreeMind:'

    def Generate_TCs_from_TDS(self, file, node_list='', reuse_tc='0', link_rule='BY_TDS_ID_THEN_SMART_NAME',
                              suite_structure='TDS'):
        """
        The generated xml file need to be imported into testlink manually.
        """
        self.logger.info(self.log_prefix + "Starting to export %s to xml file." % file)
        tc_tds_dict = {}
        tc_pfs_dict = {}

        fm_tree = lxmlET.parse(file)
        tds_root = fm_tree.getroot()
        node_list = node_list.split('|')
        node_list = [item.strip() for item in node_list]

        tc_root = lxmlET.Element('testsuite', {'name': ''})
        lxmlET.SubElement(tc_root, 'node_order').text = lxmlET.CDATA('')
        lxmlET.SubElement(tc_root, 'details').text = lxmlET.CDATA('')
        self._gen_tc_xml_from_tds(tc_root, tds_root, tc_tds_dict, tc_pfs_dict, node_list, reuse_tc, link_rule,
                                  suite_structure)
        xml_file_name = file[:-2] + 'xml'

        f = open(xml_file_name, 'wb')
        f.write(lxmlET.tostring(tc_root, xml_declaration=True, encoding='utf-8', pretty_print=True))
        f.close()
        self.logger.info(self.log_prefix + \
                         "Successfully generated the test cases xml file (%s).\n\n\n\n" % xml_file_name)

    def _gen_tc_xml_from_tds(self, ts_node, root_node, tc_tds_dict, tc_pfs_dict, node_list,
                             reuse_tc, link_rule, suite_structure):
        existing_tc_list = []
        if node_list == ['']:
            self.logger.info(self.log_prefix + \
                             "Generating test cases xml file for all TDS nodes.")
            self._gen_tc_xml_from_tds_node(ts_node, root_node, tc_tds_dict, tc_pfs_dict, existing_tc_list,
                                           reuse_tc, link_rule, suite_structure)
            return
        for tds_item in root_node.iter('node'):
            if tds_item.attrib['ID'] in node_list:
                self.logger.info(self.log_prefix + \
                                 "Generating test cases xml file for TDS node (%s)." % \
                                 (tds_item.attrib['ID']))
                child_ts_node = lxmlET.SubElement(ts_node, 'testsuite', {'name': tds_item.attrib['TEXT'].strip()})
                lxmlET.SubElement(child_ts_node, 'node_order').text = lxmlET.CDATA('')
                lxmlET.SubElement(child_ts_node, 'details').text = lxmlET.CDATA('')
                self._gen_tc_xml_from_tds_node(child_ts_node, tds_item, tc_tds_dict, tc_pfs_dict, existing_tc_list,
                                               reuse_tc, link_rule, suite_structure)

    def _gen_tc_xml_from_tds_node(self, ts_node, root_node, tc_tds_dict, tc_pfs_dict, existing_tc_list,
                                  reuse_tc, link_rule, suite_structure):
        ts_node_order = -1
        tc_node_order = -1
        for tds_item in root_node.findall('node'):
            if tds_item.attrib.has_key('LINK'):
                continue
            is_testsuite = False
            has_steps = False
            for item_icon in tds_item.findall('icon'):
                # if item_icon.attrib['BUILTIN'] == 'flag':
                # ?????????????????????icon????????????????????????????????????flag-blue???flag-orange???flag????????????str.startswith??????????????????
                if item_icon.attrib['BUILTIN'].startswith('flag'):
                    ts_node_order += 1
                    child_ts_node = lxmlET.SubElement(ts_node, 'testsuite', {'name': tds_item.attrib['TEXT'].strip()})
                    self.logger.info(
                        self.log_prefix + "Creating Test Suite   [%s]" % tds_item.attrib['TEXT'].strip())
                    lxmlET.SubElement(child_ts_node, 'node_order').text = lxmlET.CDATA(str(ts_node_order))
                    lxmlET.SubElement(child_ts_node, 'details').text = lxmlET.CDATA('')
                    # ts_node = child_ts_node
                    is_testsuite = True
                    break
                '''???????????????????????????????????????'''
                if item_icon in tds_item.findall('icon'):
                    # if item_icon.attrib['BUILTIN'] == 'bookmark':
                    if item_icon.attrib['BUILTIN'].strip().count('full-') >= 1:
                        tc_node_order += 1
                        step_ts_node = lxmlET.SubElement(ts_node, 'testcase',
                                                         {'name': str(tds_item.attrib['TEXT'])})
                        has_steps = True
                        break

            if is_testsuite:
                self._gen_tc_xml_from_tds_node(child_ts_node, tds_item, tc_tds_dict, tc_pfs_dict, existing_tc_list,
                                               reuse_tc, link_rule, suite_structure)
                continue
            '''????????????????????????????????????'''
            # ?????????????????????
            if has_steps:
                self.logger.info(
                    self.log_prefix + "Generating Test case       -<has steps> %s" % str(tds_item.attrib['TEXT']))
                lxmlET.SubElement(step_ts_node, 'node_order').text = lxmlET.CDATA(str(tc_node_order))
                lxmlET.SubElement(step_ts_node, 'externalid').text = lxmlET.CDATA('')
                lxmlET.SubElement(step_ts_node, 'version').text = lxmlET.CDATA('1')
                lxmlET.SubElement(step_ts_node, 'summary').text = lxmlET.CDATA(str(tds_item.attrib['TEXT']))
                lxmlET.SubElement(step_ts_node, 'execution_type').text = lxmlET.CDATA('1')

                # ??????freemind????????????
                for fm_preconitions in tds_item.findall('richcontent'):
                    for child in fm_preconitions.findall('html'):
                        for children in child.findall('body'):
                            for grandchild in children.findall('p'):
                                self._getpreconditions(step_ts_node, grandchild)
                            if grandchild is None:
                                self._getpreconditions(step_ts_node, children)
                # ??????xmind????????????
                for xm_preconitions in tds_item.findall('hook'):
                    for child in xm_preconitions.findall('text'):
                        self._getpreconditions(step_ts_node, child)

                node_reg_lvl = 2
                for node_icon in tds_item.findall('icon'):
                    if node_icon.attrib['BUILTIN'].strip().count('full-') == 1:
                        node_reg_lvl = 4 - int(node_icon.attrib['BUILTIN'].strip()[-1])
                if node_reg_lvl < 1:
                    node_reg_lvl = 2
                lxmlET.SubElement(step_ts_node, 'importance').text = lxmlET.CDATA(str(node_reg_lvl))
                # print(type(step_ts_node))
                '''xml??????steps'''
                steps = lxmlET.SubElement(step_ts_node, 'steps')
                '''????????????step'''
                sn = 1

                # ??????????????????????????????????????????
                for item in tds_item.findall('node'):
                    # ???????????????
                    # global step
                    step = lxmlET.SubElement(steps, 'step')
                    lxmlET.SubElement(step, 'step_number').text = lxmlET.CDATA(str(sn))
                    stritem = str(item.attrib['TEXT'])
                    count1 = stritem.count('\n')
                    if count1 > 0:
                        stritem = stritem.replace('\n', '<br />', count1)
                    lxmlET.SubElement(step, 'actions').text = lxmlET.CDATA(stritem)
                    self.logger.info(self.log_prefix + "add Step actions               %s" % stritem)
                    for child1 in item:
                        # if child1.get('TEXT') is not None:
                        # ?????????????????????
                        stritemchild = str(child1.attrib['TEXT'])
                        count2 = stritemchild.count('\n')
                        if count2 > 0:
                            stritemchild = stritemchild.replace('\n', '<br />', count2)
                        lxmlET.SubElement(step, 'expectedresults').text = lxmlET.CDATA(stritemchild)
                        self.logger.info(self.log_prefix + "add Expected Results           ->%s" % stritemchild)
                    lxmlET.SubElement(step, 'execution_type').text = lxmlET.CDATA('1')
                    sn += 1
                continue

            if not _last_tds_node(tds_item):
                self._gen_tc_xml_from_tds_node(ts_node, tds_item, tc_tds_dict, tc_pfs_dict, existing_tc_list,
                                               reuse_tc, link_rule, suite_structure)
                continue
            # This must be the last TDS node
            tc_list = []
            if not tc_list:
                # There is no linked test case nodes (which mainly used for reusing test cases between projects)
                if tds_item.attrib['ID'].strip() in existing_tc_list:
                    continue
                existing_tc_list.append(tds_item.attrib['ID'].strip())
                tc_node_order += 1
                self._add_dummy_testcase(ts_node, tds_item, tc_tds_dict, tc_pfs_dict, tc_node_order)

            # If this node already have test cases associated, update its traceability if necessary.
            # Get the test case from original xml file and copy it into the new xml file
            for tc_id in tc_list:
                if tc_id in existing_tc_list:
                    continue
                existing_tc_list.append(tc_id)
                tc_node_order += 1
                # tc_node = self._get_tc_node_from_xml_by_id(self.based_tc_url, tc_id)
                if tc_node is None:
                    return
                # res = self._update_tc_node(tc_node, tc_node_order, tds_item, tc_tds_dict, tc_pfs_dict, tc_id)
                ts_node.append(tc_node)

    # ????????????
    def _getpreconditions(self, step_name, node_name):
        lxmlET.SubElement(step_name, 'preconditions').text = lxmlET.CDATA(node_name.text)

    def _add_dummy_testcase(self, ts_node, tds_item, tc_tds_dict, tc_pfs_dict, tc_node_order):
        if not tds_item.attrib.has_key('TEXT'):
            self.logger.error(self.log_prefix + \
                              "Please check node (%s) since it may use a long name. Please convert it to plain text via FreeMind Menu Format=>Use Plaine Text." % \
                              (tds_item.attrib['ID'].strip()))
            exit(-1)
        tds_item_str = str(tds_item.attrib['TEXT']).split('&')
        self.logger.info(self.log_prefix + "Generating test case       -%s" % tds_item_str[0])
        node_reg_lvl = 2
        for node_icon in tds_item.findall('icon'):
            if node_icon.attrib['BUILTIN'].strip().count('full-') == 1:
                node_reg_lvl = 4 - int(node_icon.attrib['BUILTIN'].strip()[-1])
            if node_reg_lvl < 1:
                node_reg_lvl = 2
        testcase = lxmlET.SubElement(ts_node, 'testcase', {'name': tds_item_str[0]})
        lxmlET.SubElement(testcase, 'node_order').text = lxmlET.CDATA(str(tc_node_order))
        lxmlET.SubElement(testcase, 'externalid').text = lxmlET.CDATA('')
        lxmlET.SubElement(testcase, 'version').text = lxmlET.CDATA('1')
        lxmlET.SubElement(testcase, 'summary').text = lxmlET.CDATA(tds_item_str[0])
        lxmlET.SubElement(testcase, 'execution_type').text = lxmlET.CDATA('1')
        lxmlET.SubElement(testcase, 'importance').text = lxmlET.CDATA(str(node_reg_lvl))
        # ??????freemind??????
        for item_preconitions in tds_item.findall('richcontent'):
            for child in item_preconitions.findall('html'):
                for children in child.findall('body'):
                    for grandchild in children.findall('p'):
                        # lxmlET.SubElement(testcase, 'preconditions').text = lxmlET.CDATA(grandchild.text)
                        self._getpreconditions(testcase, grandchild)
                    if grandchild is None:
                        # lxmlET.SubElement(testcase, 'preconditions').text = lxmlET.CDATA(children.text)
                        self._getpreconditions(testcase, children)
        # ??????xmind????????????
        for xm_preconitions in tds_item.findall('hook'):
            for child in xm_preconitions.findall('text'):
                lxmlET.SubElement(testcase, 'preconditions').text = lxmlET.CDATA(child.text)


def start_main():
    # path = os.path.dirname('./')  # for windows
    # path = os.getcwd()  # for windows
    path = os.path.dirname(sys.executable)  # for mac

    logging.basicConfig(handlers=[logging.FileHandler(path + '/logger.log', 'w', 'utf-8')],
                        format='%(asctime)s:%(levelname)s  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG,
                        )
    logger = logging.getLogger(__name__)
    console = logging.StreamHandler()  # ??????console handler
    console.setLevel(logging.INFO)  # ?????????handler??????
    formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')  # ?????????handler??????
    console.setFormatter(formatter)
    # Create an instance
    logging.getLogger().addHandler(console)

    file_list = get_freeplanefile(path)
    for file in file_list:
        FreeMind(logger).Generate_TCs_from_TDS(file)


if __name__ == '__main__':
    start_main()
