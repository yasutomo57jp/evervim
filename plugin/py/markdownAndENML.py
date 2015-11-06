# encoding: utf-8
# vim: sts=4 sw=4 fdm=marker
# Author: kakkyz <kakkyz81@gmail.com>
# License: MIT
import markdown
from markdown.extensions.sane_lists import SaneListExtension
import xml.sax.saxutils
import re


class parserOption:  # {{{
    def __init__(self):
        self.a          = False
        self.ul         = False
        self.ol         = False
        self.li         = False
        self.pre        = False
        self.code       = False
        self.p          = False
        self.blockquote = 0
        self.count      = 0
        self.liststack = []

    def __str__(self):
        return "a={0} ul={1} ol={2} li={3} pre={4} code={5} p={6} blockquote={7} count={8} ".format(self.a,
               self.ul,
               self.ol,
               self.li,
               self.pre,
               self.code,
               self.p,
               self.blockquote,
               self.count)
#}}}

removeheadercode = re.compile('^<code>')
removefootercode = re.compile('</code>$')


def parseENML(node, level=0, result='', option=parserOption()):  # {{{
# import html2text
#   return html2text.html2text(node.toxml())
#   print node.toxml()
#   print "{0}:{1}:{2}:{3}:{4}:{5}".format(
#           level ,
#           _getNodeType(node) ,
#           _getTagName(node),
#           _getAttribute(node),
#           _getData(node), option)
    if node.nodeType == node.ELEMENT_NODE:
        tag = _getTagName(node)
        if tag == "a":
            htmlhref = _getAttribute(node)
            option.a = True
            htmltext = "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
            option.a = False
#           result += '[{0}]({1})'.format(htmltext, htmlhref) # this code does not work multibyte!
            result += '[{' + htmltext + '}]({' + htmlhref + '})'
        elif tag == "ul":
            option.ul = True
            if len(option.liststack) == 0:
                result += "\n"
            option.liststack.append(("ul", option.count))
            result += "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
            _type, option.count = option.liststack.pop()
            if len(option.liststack) == 0:
                result += "\n"
            option.ul = False
        elif tag == "ol":
            option.ol = True
            if len(option.liststack) == 0:
                result += "\n"
            option.liststack.append(("ol", option.count))
            option.count = 0
            result += "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
            _type, option.count = option.liststack.pop()
            if len(option.liststack) == 0:
                result += "\n"
            option.ol = False
        elif tag == "pre":
            option.pre = True
            result += "".join([parseENML(child, level + 1, result, option) for child in node.childNodes])
            option.pre = False
        elif tag == "code":
            option.code = True
            if option.pre == True:
                precode = removeheadercode.sub('', xml.sax.saxutils.unescape(node.toxml()))
                precode = removefootercode.sub('', precode)
                for line in precode.splitlines():
                    result += "    %s\n" % line.rstrip()
                result += "\n"
            else:
                incode = removeheadercode.sub('`', xml.sax.saxutils.unescape(node.toxml()))
                incode = removefootercode.sub('`', incode)
                result += incode
            option.code = False
        elif tag == "p":
            option.p = True
            result += "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
            result += "\n"
            option.p = False
        elif tag == "li":
            option.count += 1
            #########if option.ul:
            depth = len(option.liststack)-1
            if option.liststack[-1][0] == "ul":
                result += "\t"*depth + "* " + "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
            elif option.liststack[-1][0] == "ol":
                result += "\t"*depth + str(option.count) + ". " + "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
        elif tag == "blockquote":
            option.blockquote += 1
            result += "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
            result += "\n"
            option.blockquote -= 1
        elif tag == "hr":
            result += "----\n"
        elif tag in ["img", "en-media", "en-todo", "en-crypt"]:  # 後で改行を除去して見やすくする？
            return node.toxml() + "\n"
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            headerlv = tag[1:]
            result += ("#" * int(headerlv)) + " " + "".join([parseENML(child, level + 1, "", option) for child in node.childNodes])
        else:
            result += "".join([parseENML(child, level + 1, result, option) for child in node.childNodes])
    elif node.nodeType == node.TEXT_NODE:
        if _getData(node).strip():
            if option.blockquote > 0:
                result += "> " * option.blockquote + _getData(node)
            else:
                result += _getData(node)
#           if not ( option.a == True or option.code == False ):
            if option.a == False:
                result += "\n"
    return result
#}}}


def parseMarkdown(mkdtext):  # {{{
    m = markdown.markdown(mkdtext.decode('utf-8'), extensions=[SaneListExtension()])
    return m
#}}}

# ----- private methods


def _getTagName(node):  # {{{
    if node.nodeType == node.ELEMENT_NODE:
        return node.tagName
    return None
#}}}


def _getData(node):  # {{{
    """ return textdata """
    if node.nodeType == node.TEXT_NODE:
        return node.data.strip()
    return ""
#}}}


def _getAttribute(node):  # {{{
    try:
        if _getTagName(node) == "a":
            return node.getAttribute("href")
    except:
        pass
    return None
#}}}


def _getNodeType(node):  # {{{
    """ return NodeType as String """
    if   node.nodeType == node.ELEMENT_NODE                    : return   "ELEMENT_NODE"
    elif node.nodeType == node.ATTRIBUTE_NODE                  : return   "ATTRIBUTE_NODE"
    elif node.nodeType == node.TEXT_NODE                       : return   "TEXT_NODE"
    elif node.nodeType == node.CDATA_SECTION_NODE              : return   "CDATA_SECTION_NODE"
    elif node.nodeType == node.ENTITY_NODE                     : return   "ENTITY_NODE"
    elif node.nodeType == node.PROCESSING_INSTRUCTION_NODE     : return   "PROCESSING_INSTRUCTION_NODE"
    elif node.nodeType == node.COMMENT_NODE                    : return   "COMMENT_NODE"
    elif node.nodeType == node.DOCUMENT_NODE                   : return   "DOCUMENT_NODE"
    elif node.nodeType == node.DOCUMENT_TYPE_NODE              : return   "DOCUMENT_TYPE_NODE"
    elif node.nodeType == node.NOTATION_NODE                   : return   "NOTATION_NODE"
    return "UKNOWN NODE"
#}}}

if __name__ == "__main__":
    import doctest
    doctest.testmod()
