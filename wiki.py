import bottle
import yaml
import datetime
import copy
import difflib
import re
import itertools
import os
import sys
import signal
import time
import multiprocessing
import logging
import ConfigParser
from bottle import delete, get, post, put, run, template
from os.path import expanduser

logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wiki.log'), level=logging.DEBUG)

config = ConfigParser.RawConfigParser()
config.read(os.path.join(expanduser('~'), '.genwikirc'))

WIKI_FILE = config.get('wiki', 'file') or os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wiki.yaml')
logging.info('Using wiki file: %s', WIKI_FILE)
WIKI_HOST = 'localhost'
WIKI_PORT = 8088

marked_js = """
/**
 * marked - a markdown parser
 * Copyright (c) 2011-2014, Christopher Jeffrey. (MIT Licensed)
 * https://github.com/chjj/marked
 */
(function(){var block={newline:/^\\n+/,code:/^( {4}[^\\n]+\\n*)+/,fences:noop,hr:/^( *[-*_]){3,} *(?:\\n+|$)/,heading:/^ *(#{1,6}) *([^\\n]+?) *#* *(?:\\n+|$)/,nptable:noop,lheading:/^([^\\n]+)\\n *(=|-){2,} *(?:\\n+|$)/,blockquote:/^( *>[^\\n]+(\\n(?!def)[^\\n]+)*\\n*)+/,list:/^( *)(bull) [\\s\\S]+?(?:hr|def|\\n{2,}(?! )(?!\\1bull )\\n*|\\s*$)/,html:/^ *(?:comment|closed|closing) *(?:\\n{2,}|\\s*$)/,def:/^ *\\[([^\\]]+)\\]: *<?([^\\s>]+)>?(?: +["(]([^\\n]+)[")])? *(?:\\n+|$)/,table:noop,paragraph:/^((?:[^\\n]+\\n?(?!hr|heading|lheading|blockquote|tag|def))+)\\n*/,text:/^[^\\n]+/};block.bullet=/(?:[*+-]|\\d+\\.)/;block.item=/^( *)(bull) [^\\n]*(?:\\n(?!\\1bull )[^\\n]*)*/;block.item=replace(block.item,"gm")(/bull/g,block.bullet)();block.list=replace(block.list)(/bull/g,block.bullet)("hr","\\\\n+(?=\\\\1?(?:[-*_] *){3,}(?:\\\\n+|$))")("def","\\\\n+(?="+block.def.source+")")();block.blockquote=replace(block.blockquote)("def",block.def)();block._tag="(?!(?:"+"a|em|strong|small|s|cite|q|dfn|abbr|data|time|code"+"|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo"+"|span|br|wbr|ins|del|img)\\\\b)\\\\w+(?!:/|[^\\\\w\\\\s@]*@)\\\\b";block.html=replace(block.html)("comment",/<!--[\\s\\S]*?-->/)("closed",/<(tag)[\\s\\S]+?<\\/\\1>/)("closing",/<tag(?:"[^"]*"|'[^']*'|[^'">])*?>/)(/tag/g,block._tag)();block.paragraph=replace(block.paragraph)("hr",block.hr)("heading",block.heading)("lheading",block.lheading)("blockquote",block.blockquote)("tag","<"+block._tag)("def",block.def)();block.normal=merge({},block);block.gfm=merge({},block.normal,{fences:/^ *(`{3,}|~{3,}) *(\\S+)? *\\n([\\s\\S]+?)\\s*\\1 *(?:\\n+|$)/,paragraph:/^/});block.gfm.paragraph=replace(block.paragraph)("(?!","(?!"+block.gfm.fences.source.replace("\\\\1","\\\\2")+"|"+block.list.source.replace("\\\\1","\\\\3")+"|")();block.tables=merge({},block.gfm,{nptable:/^ *(\\S.*\\|.*)\\n *([-:]+ *\\|[-| :]*)\\n((?:.*\\|.*(?:\\n|$))*)\\n*/,table:/^ *\\|(.+)\\n *\\|( *[-:]+[-| :]*)\\n((?: *\\|.*(?:\\n|$))*)\\n*/});
function Lexer(options){this.tokens=[];this.tokens.links={};this.options=options||marked.defaults;this.rules=block.normal;if(this.options.gfm){if(this.options.tables){this.rules=block.tables}else{this.rules=block.gfm}}}Lexer.rules=block;Lexer.lex=function(src,options){var lexer=new Lexer(options);return lexer.lex(src)};Lexer.prototype.lex=function(src){src=src.replace(/\\r\\n|\\r/g,"\\n").replace(/\\t/g,"    ").replace(/\\u00a0/g," ").replace(/\\u2424/g,"\\n");return this.token(src,true)};Lexer.prototype.token=function(src,top,bq){var src=src.replace(/^ +$/gm,""),next,loose,cap,bull,b,item,space,i,l;while(src){if(cap=this.rules.newline.exec(src)){src=src.substring(cap[0].length);if(cap[0].length>1){this.tokens.push({type:"space"})}}if(cap=this.rules.code.exec(src)){src=src.substring(cap[0].length);cap=cap[0].replace(/^ {4}/gm,"");this.tokens.push({type:"code",text:!this.options.pedantic?cap.replace(/\\n+$/,""):cap});continue}if(cap=this.rules.fences.exec(src)){src=src.substring(cap[0].length);this.tokens.push({type:"code",lang:cap[2],text:cap[3]});continue}if(cap=this.rules.heading.exec(src)){src=src.substring(cap[0].length);this.tokens.push({type:"heading",depth:cap[1].length,text:cap[2]});continue}if(top&&(cap=this.rules.nptable.exec(src))){src=src.substring(cap[0].length);item={type:"table",header:cap[1].replace(/^ *| *\\| *$/g,"").split(/ *\\| */),align:cap[2].replace(/^ *|\\| *$/g,"").split(/ *\\| */),cells:cap[3].replace(/\\n$/,"").split("\\n")};for(i=0;i<item.align.length;i++){if(/^ *-+: *$/.test(item.align[i])){item.align[i]="right"}else if(/^ *:-+: *$/.test(item.align[i])){item.align[i]="center"}else if(/^ *:-+ *$/.test(item.align[i])){item.align[i]="left"}else{item.align[i]=null}}for(i=0;i<item.cells.length;i++){item.cells[i]=item.cells[i].split(/ *\\| */)}this.tokens.push(item);continue}if(cap=this.rules.lheading.exec(src)){src=src.substring(cap[0].length);
this.tokens.push({type:"heading",depth:cap[2]==="="?1:2,text:cap[1]});continue}if(cap=this.rules.hr.exec(src)){src=src.substring(cap[0].length);this.tokens.push({type:"hr"});continue}if(cap=this.rules.blockquote.exec(src)){src=src.substring(cap[0].length);this.tokens.push({type:"blockquote_start"});cap=cap[0].replace(/^ *> ?/gm,"");this.token(cap,top,true);this.tokens.push({type:"blockquote_end"});continue}if(cap=this.rules.list.exec(src)){src=src.substring(cap[0].length);bull=cap[2];this.tokens.push({type:"list_start",ordered:bull.length>1});cap=cap[0].match(this.rules.item);next=false;l=cap.length;i=0;for(;i<l;i++){item=cap[i];space=item.length;item=item.replace(/^ *([*+-]|\\d+\\.) +/,"");if(~item.indexOf("\\n ")){space-=item.length;item=!this.options.pedantic?item.replace(new RegExp("^ {1,"+space+"}","gm"),""):item.replace(/^ {1,4}/gm,"")}if(this.options.smartLists&&i!==l-1){b=block.bullet.exec(cap[i+1])[0];if(bull!==b&&!(bull.length>1&&b.length>1)){src=cap.slice(i+1).join("\\n")+src;i=l-1}}loose=next||/\\n\\n(?!\\s*$)/.test(item);if(i!==l-1){next=item.charAt(item.length-1)==="\\n";if(!loose)loose=next}this.tokens.push({type:loose?"loose_item_start":"list_item_start"});this.token(item,false,bq);this.tokens.push({type:"list_item_end"})}this.tokens.push({type:"list_end"});continue}if(cap=this.rules.html.exec(src)){src=src.substring(cap[0].length);this.tokens.push({type:this.options.sanitize?"paragraph":"html",pre:cap[1]==="pre"||cap[1]==="script"||cap[1]==="style",text:cap[0]});continue}if(!bq&&top&&(cap=this.rules.def.exec(src))){src=src.substring(cap[0].length);this.tokens.links[cap[1].toLowerCase()]={href:cap[2],title:cap[3]};continue}
if(top&&(cap=this.rules.table.exec(src))){src=src.substring(cap[0].length);item={type:"table",header:cap[1].replace(/^ *| *\\| *$/g,"").split(/ *\\| */),align:cap[2].replace(/^ *|\\| *$/g,"").split(/ *\\| */),cells:cap[3].replace(/(?: *\\| *)?\\n$/,"").split("\\n")};for(i=0;i<item.align.length;i++){if(/^ *-+: *$/.test(item.align[i])){item.align[i]="right"}else if(/^ *:-+: *$/.test(item.align[i])){item.align[i]="center"}else if(/^ *:-+ *$/.test(item.align[i])){item.align[i]="left"}else{item.align[i]=null}}for(i=0;i<item.cells.length;i++){item.cells[i]=item.cells[i].replace(/^ *\\| *| *\\| *$/g,"").split(/ *\\| */)}this.tokens.push(item);continue}if(top&&(cap=this.rules.paragraph.exec(src))){src=src.substring(cap[0].length);this.tokens.push({type:"paragraph",text:cap[1].charAt(cap[1].length-1)==="\\n"?cap[1].slice(0,-1):cap[1]});continue}if(cap=this.rules.text.exec(src)){src=src.substring(cap[0].length);this.tokens.push({type:"text",text:cap[0]});continue}if(src){throw new Error("Infinite loop on byte: "+src.charCodeAt(0))}}return this.tokens};var inline={escape:/^\\\\([\\\\`*{}\\[\\]()#+\\-.!_>])/,autolink:/^<([^ >]+(@|:\\/)[^ >]+)>/,url:noop,tag:/^<!--[\\s\\S]*?-->|^<\\/?\\w+(?:"[^"]*"|'[^']*'|[^'">])*?>/,link:/^!?\\[(inside)\\]\\(href\\)/,reflink:/^!?\\[(inside)\\]\\s*\\[([^\\]]*)\\]/,nolink:/^!?\\[((?:\\[[^\\]]*\\]|[^\\[\\]])*)\\]/,strong:/^__([\\s\\S]+?)__(?!_)|^\\*\\*([\\s\\S]+?)\\*\\*(?!\\*)/,em:/^\\b_((?:__|[\\s\\S])+?)_\\b|^\\*((?:\\*\\*|[\\s\\S])+?)\\*(?!\\*)/,code:/^(`+)\\s*([\\s\\S]*?[^`])\\s*\\1(?!`)/,br:/^ {2,}\\n(?!\\s*$)/,del:noop,text:/^[\\s\\S]+?(?=[\\\\<!\\[_*`]| {2,}\\n|$)/};inline._inside=/(?:\\[[^\\]]*\\]|[^\\[\\]]|\\](?=[^\\[]*\\]))*/;inline._href=/\\s*<?([\\s\\S]*?)>?(?:\\s+['"]([\\s\\S]*?)['"])?\\s*/;inline.link=replace(inline.link)("inside",inline._inside)("href",inline._href)();inline.reflink=replace(inline.reflink)("inside",inline._inside)();inline.normal=merge({},inline);inline.pedantic=merge({},inline.normal,{strong:/^__(?=\\S)([\\s\\S]*?\\S)__(?!_)|^\\*\\*(?=\\S)([\\s\\S]*?\\S)\\*\\*(?!\\*)/,em:/^_(?=\\S)([\\s\\S]*?\\S)_(?!_)|^\\*(?=\\S)([\\s\\S]*?\\S)\\*(?!\\*)/});
inline.gfm=merge({},inline.normal,{escape:replace(inline.escape)("])","~|])")(),url:/^(https?:\\/\\/[^\\s<]+[^<.,:;"')\\]\\s])/,del:/^~~(?=\\S)([\\s\\S]*?\\S)~~/,text:replace(inline.text)("]|","~]|")("|","|https?://|")()});inline.breaks=merge({},inline.gfm,{br:replace(inline.br)("{2,}","*")(),text:replace(inline.gfm.text)("{2,}","*")()});function InlineLexer(links,options){this.options=options||marked.defaults;this.links=links;this.rules=inline.normal;this.renderer=this.options.renderer||new Renderer;this.renderer.options=this.options;if(!this.links){throw new Error("Tokens array requires a `links` property.")}if(this.options.gfm){if(this.options.breaks){this.rules=inline.breaks}else{this.rules=inline.gfm}}else if(this.options.pedantic){this.rules=inline.pedantic}}InlineLexer.rules=inline;InlineLexer.output=function(src,links,options){var inline=new InlineLexer(links,options);return inline.output(src)};InlineLexer.prototype.output=function(src){var out="",link,text,href,cap;while(src){if(cap=this.rules.escape.exec(src)){src=src.substring(cap[0].length);out+=cap[1];continue}if(cap=this.rules.autolink.exec(src)){src=src.substring(cap[0].length);if(cap[2]==="@"){text=cap[1].charAt(6)===":"?this.mangle(cap[1].substring(7)):this.mangle(cap[1]);href=this.mangle("mailto:")+text}else{text=escape(cap[1]);
href=text}out+=this.renderer.link(href,null,text);continue}if(!this.inLink&&(cap=this.rules.url.exec(src))){src=src.substring(cap[0].length);text=escape(cap[1]);href=text;out+=this.renderer.link(href,null,text);continue}if(cap=this.rules.tag.exec(src)){if(!this.inLink&&/^<a /i.test(cap[0])){this.inLink=true}else if(this.inLink&&/^<\\/a>/i.test(cap[0])){this.inLink=false}src=src.substring(cap[0].length);out+=this.options.sanitize?escape(cap[0]):cap[0];continue}if(cap=this.rules.link.exec(src)){src=src.substring(cap[0].length);this.inLink=true;out+=this.outputLink(cap,{href:cap[2],title:cap[3]});this.inLink=false;continue}if((cap=this.rules.reflink.exec(src))||(cap=this.rules.nolink.exec(src))){src=src.substring(cap[0].length);link=(cap[2]||cap[1]).replace(/\\s+/g," ");link=this.links[link.toLowerCase()];if(!link||!link.href){out+=cap[0].charAt(0);src=cap[0].substring(1)+src;continue}this.inLink=true;out+=this.outputLink(cap,link);this.inLink=false;continue}if(cap=this.rules.strong.exec(src)){src=src.substring(cap[0].length);out+=this.renderer.strong(this.output(cap[2]||cap[1]));continue}if(cap=this.rules.em.exec(src)){src=src.substring(cap[0].length);out+=this.renderer.em(this.output(cap[2]||cap[1]));continue}if(cap=this.rules.code.exec(src)){src=src.substring(cap[0].length);out+=this.renderer.codespan(escape(cap[2],true));continue}if(cap=this.rules.br.exec(src)){src=src.substring(cap[0].length);
out+=this.renderer.br();continue}if(cap=this.rules.del.exec(src)){src=src.substring(cap[0].length);out+=this.renderer.del(this.output(cap[1]));continue}if(cap=this.rules.text.exec(src)){src=src.substring(cap[0].length);out+=escape(this.smartypants(cap[0]));continue}if(src){throw new Error("Infinite loop on byte: "+src.charCodeAt(0))}}return out};InlineLexer.prototype.outputLink=function(cap,link){var href=escape(link.href),title=link.title?escape(link.title):null;return cap[0].charAt(0)!=="!"?this.renderer.link(href,title,this.output(cap[1])):this.renderer.image(href,title,escape(cap[1]))};
InlineLexer.prototype.smartypants=function(text){if(!this.options.smartypants)return text;return text.replace(/--/g,"--").replace(/(^|[-\\u2014/(\\[{"\\s])'/g,"$1'")
.replace(/'/g,"'").replace(/(^|[-\\u2014/(\\[{\\u2018\\s])"/g,"$1\\"").replace(/"/g,"\\"").replace(/\\.{3}/g,"...")};
InlineLexer.prototype.mangle=function(text){var out="",l=text.length,i=0,ch;for(;i<l;i++){ch=text.charCodeAt(i);if(Math.random()>.5){ch="x"+ch.toString(16)}out+="&#"+ch+";"}return out};function Renderer(options){this.options=options||{}}Renderer.prototype.code=function(code,lang,escaped){if(this.options.highlight){var out=this.options.highlight(code,lang);if(out!=null&&out!==code){escaped=true;code=out}}if(!lang){return"<pre><code>"+(escaped?code:escape(code,true))+"\\n</code></pre>"}return'<pre><code class="'+this.options.langPrefix+escape(lang,true)+'">'+(escaped?code:escape(code,true))+"\\n</code></pre>\\n"};Renderer.prototype.blockquote=function(quote){return"<blockquote>\\n"+quote+"</blockquote>\\n"};Renderer.prototype.html=function(html){return html};Renderer.prototype.heading=function(text,level,raw){return"<h"+level+' id="'+this.options.headerPrefix+raw.toLowerCase().replace(/[^\\w]+/g,"-")+'">'+text+"</h"+level+">\\n"};Renderer.prototype.hr=function(){return this.options.xhtml?"<hr/>\\n":"<hr>\\n"};Renderer.prototype.list=function(body,ordered){var type=ordered?"ol":"ul";return"<"+type+">\\n"+body+"</"+type+">\\n"};Renderer.prototype.listitem=function(text){return"<li>"+text+"</li>\\n"};Renderer.prototype.paragraph=function(text){return"<p>"+text+"</p>\\n"};
Renderer.prototype.table=function(header,body){return"<table>\\n"+"<thead>\\n"+header+"</thead>\\n"+"<tbody>\\n"+
body+"</tbody>\\n"+"</table>\\n"};Renderer.prototype.tablerow=function(content){return"<tr>\\n"+content+"</tr>\\n"};
Renderer.prototype.tablecell=function(content,flags){var type=flags.header?"th":"td";var tag=flags.align?"<"+type+' style="text-align:'+flags.align+'">':"<"+type+">";return tag+content+"</"+type+">\\n"};
Renderer.prototype.strong=function(text){return"<strong>"+text+"</strong>"};Renderer.prototype.em=function(text){return"<em>"+text+"</em>"};Renderer.prototype.codespan=function(text){return"<code>"+text+"</code>"};Renderer.prototype.br=function(){return this.options.xhtml?"<br/>":"<br>"};Renderer.prototype.del=function(text){return"<del>"+text+"</del>"};Renderer.prototype.link=function(href,title,text){if(this.options.sanitize){try{var prot=decodeURIComponent(unescape(href)).replace(/[^\\w:]/g,"").toLowerCase()}catch(e){return""}if(prot.indexOf("javascript:")===0){return""}}var out='<a href="'+href+'"';if(title){out+=' title="'+title+'"'}out+=">"+text+"</a>";return out};Renderer.prototype.image=function(href,title,text){var out='<img src="'+href+'" alt="'+text+'"';if(title){out+=' title="'+title+'"'}out+=this.options.xhtml?"/>":">";
return out};function Parser(options){this.tokens=[];this.token=null;this.options=options||marked.defaults;this.options.renderer=this.options.renderer||new Renderer;this.renderer=this.options.renderer;this.renderer.options=this.options}Parser.parse=function(src,options,renderer){var parser=new Parser(options,renderer);return parser.parse(src)};Parser.prototype.parse=function(src){this.inline=new InlineLexer(src.links,this.options,this.renderer);this.tokens=src.reverse();var out="";while(this.next()){out+=this.tok()}return out};Parser.prototype.next=function(){return this.token=this.tokens.pop()};Parser.prototype.peek=function(){return this.tokens[this.tokens.length-1]||0};Parser.prototype.parseText=function(){var body=this.token.text;while(this.peek().type==="text"){body+="\\n"+this.next().text}return this.inline.output(body)};Parser.prototype.tok=function(){switch(this.token.type){case"space":{return""}case"hr":{return this.renderer.hr()}case"heading":{return this.renderer.heading(this.inline.output(this.token.text),this.token.depth,this.token.text)}case"code":{return this.renderer.code(this.token.text,this.token.lang,this.token.escaped)}case"table":{var header="",body="",i,row,cell,flags,j;cell="";
for(i=0;i<this.token.header.length;i++){flags={header:true,align:this.token.align[i]};cell+=this.renderer.tablecell(this.inline.output(this.token.header[i]),{header:true,align:this.token.align[i]})}header+=this.renderer.tablerow(cell);for(i=0;i<this.token.cells.length;i++){row=this.token.cells[i];cell="";for(j=0;j<row.length;j++){cell+=this.renderer.tablecell(this.inline.output(row[j]),{header:false,align:this.token.align[j]})}body+=this.renderer.tablerow(cell)}return this.renderer.table(header,body)}case"blockquote_start":{var body="";while(this.next().type!=="blockquote_end"){body+=this.tok()}return this.renderer.blockquote(body)}case"list_start":{var body="",ordered=this.token.ordered;while(this.next().type!=="list_end"){body+=this.tok()}return this.renderer.list(body,ordered)}case"list_item_start":{var body="";while(this.next().type!=="list_item_end"){body+=this.token.type==="text"?this.parseText():this.tok()}return this.renderer.listitem(body)}case"loose_item_start":{var body="";while(this.next().type!=="list_item_end"){body+=this.tok()}return this.renderer.listitem(body)}case"html":{var html=!this.token.pre&&!this.options.pedantic?this.inline.output(this.token.text):this.token.text;return this.renderer.html(html)}case"paragraph":{return this.renderer.paragraph(this.inline.output(this.token.text))}case"text":{return this.renderer.paragraph(this.parseText())}}};function escape(html,encode){return html.replace(!encode?/&(?!#?\\w+;)/g:/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function unescape(html){return html.replace(/&([#\\w]+);/g,function(_,n){n=n.toLowerCase();if(n==="colon")return":";if(n.charAt(0)==="#"){return n.charAt(1)==="x"?String.fromCharCode(parseInt(n.substring(2),16)):String.fromCharCode(+n.substring(1))}return""})}function replace(regex,opt){regex=regex.source;opt=opt||"";return function self(name,val){if(!name)return new RegExp(regex,opt);val=val.source||val;val=val.replace(/(^|[^\\[])\\^/g,"$1");regex=regex.replace(name,val);return self}}function noop(){}noop.exec=noop;function merge(obj){var i=1,target,key;for(;i<arguments.length;i++){target=arguments[i];for(key in target){if(Object.prototype.hasOwnProperty.call(target,key)){obj[key]=target[key]}}}return obj}function marked(src,opt,callback){if(callback||typeof opt==="function"){if(!callback){callback=opt;
opt=null}opt=merge({},marked.defaults,opt||{});var highlight=opt.highlight,tokens,pending,i=0;try{tokens=Lexer.lex(src,opt)}catch(e){return callback(e)}pending=tokens.length;var done=function(err){if(err){opt.highlight=highlight;return callback(err)}var out;try{out=Parser.parse(tokens,opt)}catch(e){err=e}opt.highlight=highlight;return err?callback(err):callback(null,out)};if(!highlight||highlight.length<3){return done()}delete opt.highlight;if(!pending)return done();for(;i<tokens.length;i++){(function(token){if(token.type!=="code"){return--pending||done()}return highlight(token.text,token.lang,function(err,code){if(err)return done(err);if(code==null||code===token.text){return--pending||done()}token.text=code;token.escaped=true;--pending||done()})})(tokens[i])}return}try{if(opt)opt=merge({},marked.defaults,opt);return Parser.parse(Lexer.lex(src,opt),opt)}catch(e){e.message+="\\nPlease report this to https://github.com/chjj/marked.";if((opt||marked.defaults).silent){return"<p>An error occured:</p><pre>"+escape(e.message+"",true)+"</pre>"}throw e}}marked.options=marked.setOptions=function(opt){merge(marked.defaults,opt);return marked};marked.defaults={gfm:true,tables:true,breaks:false,pedantic:false,sanitize:false,smartLists:false,silent:false,highlight:null,langPrefix:"lang-",smartypants:false,headerPrefix:"",renderer:new Renderer,xhtml:false};marked.Parser=Parser;marked.parser=Parser.parse;marked.Renderer=Renderer;marked.Lexer=Lexer;marked.lexer=Lexer.lex;marked.InlineLexer=InlineLexer;marked.inlineLexer=InlineLexer.output;marked.parse=marked;if(typeof module!=="undefined"&&typeof exports==="object"){module.exports=marked}else if(typeof define==="function"&&define.amd){define(function(){return marked})}else{this.marked=marked}}).call(function(){return this||(typeof window!=="undefined"?window:global)}());
"""

showdown_js = """/*showdown*/
var Showdown={extensions:{}};var forEach=Showdown.forEach=function(c,d){if(typeof c.forEach==="function"){c.forEach(d);}else{var b,a=c.length;for(b=0;b<a;b++){d(c[b],b,c);}}};var stdExtName=function(a){return a.replace(/[_-]||\\s/g,"").toLowerCase();};Showdown.converter=function(m){var w;var l;var a;var z=0;var i=[];var p=[];if(typeof module!=="undefind"&&typeof exports!=="undefined"&&typeof require!=="undefind"){var s=require("fs");if(s){var N=s.readdirSync((__dirname||".")+"/extensions").filter(function(P){return ~P.indexOf(".js");}).map(function(P){return P.replace(/\\.js$/,"");});Showdown.forEach(N,function(Q){var P=stdExtName(Q);Showdown.extensions[P]=require("./extensions/"+Q);});}}this.makeHtml=function(P){w={};l={};a=[];P=P.replace(/~/g,"~T");P=P.replace(/\\$/g,"~D");P=P.replace(/\\r\\n/g,"\\n");P=P.replace(/\\r/g,"\\n");P="\\n\\n"+P+"\\n\\n";P=I(P);P=P.replace(/^[ \\t]+$/mg,"");Showdown.forEach(i,function(Q){P=d(Q,P);});P=F(P);P=o(P);P=k(P);P=b(P);P=L(P);P=P.replace(/~D/g,"$$");P=P.replace(/~T/g,"~");Showdown.forEach(p,function(Q){P=d(Q,P);});return P;};if(m&&m.extensions){var g=this;Showdown.forEach(m.extensions,function(P){if(typeof P==="string"){P=Showdown.extensions[stdExtName(P)];}if(typeof P==="function"){Showdown.forEach(P(g),function(Q){if(Q.type){if(Q.type==="language"||Q.type==="lang"){i.push(Q);}else{if(Q.type==="output"||Q.type==="html"){p.push(Q);}}}else{p.push(Q);}});}else{throw"Extension '"+P+"' could not be loaded.  It was either not found or is not a valid extension.";}});}var d=function(Q,R){if(Q.regex){var P=new RegExp(Q.regex,"g");return R.replace(P,Q.replace);}else{if(Q.filter){return Q.filter(R);}}};var k=function(P){P+="~0";P=P.replace(/^[ ]{0,3}\\[(.+)\\]:[ \\t]*\\n?[ \\t]*<?(\\S+?)>?[ \\t]*\\n?[ \\t]*(?:(\\n*)["(](.+?)[")][ \\t]*)?(?:\\n+|(?=~0))/gm,function(S,U,T,R,Q){U=U.toLowerCase();w[U]=B(T);if(R){return R+Q;}else{if(Q){l[U]=Q.replace(/"/g,"&quot;");}}return"";});P=P.replace(/~0/,"");return P;};var o=function(R){R=R.replace(/\\n/g,"\\n\\n");var Q="p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|ins|del|style|section|header|footer|nav|article|aside";
var P="p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|style|section|header|footer|nav|article|aside";R=R.replace(/^(<(p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|ins|del)\\b[^\\r]*?\\n<\\/\\2>[ \\t]*(?=\\n+))/gm,O);R=R.replace(/^(<(p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|style|section|header|footer|nav|article|aside)\\b[^\\r]*?<\\/\\2>[ \\t]*(?=\\n+)\\n)/gm,O);R=R.replace(/(\\n[ ]{0,3}(<(hr)\\b([^<>])*?\\/?>)[ \\t]*(?=\\n{2,}))/g,O);R=R.replace(/(\\n\\n[ ]{0,3}<!(--[^\\r]*?--\\s*)+>[ \\t]*(?=\\n{2,}))/g,O);R=R.replace(/(?:\\n\\n)([ ]{0,3}(?:<([?%])[^\\r]*?\\2>)[ \\t]*(?=\\n{2,}))/g,O);R=R.replace(/\\n\\n/g,"\\n");return R;};var O=function(P,Q){var R=Q;R=R.replace(/\\n\\n/g,"\\n");R=R.replace(/^\\n/,"");R=R.replace(/\\n+$/g,"");R="\\n\\n~K"+(a.push(R)-1)+"K\\n\\n";return R;};var b=function(Q){Q=f(Q);var P=M("<hr />");Q=Q.replace(/^[ ]{0,2}([ ]?\\*[ ]?){3,}[ \\t]*$/gm,P);Q=Q.replace(/^[ ]{0,2}([ ]?\\-[ ]?){3,}[ \\t]*$/gm,P);Q=Q.replace(/^[ ]{0,2}([ ]?\\_[ ]?){3,}[ \\t]*$/gm,P);Q=K(Q);Q=q(Q);Q=c(Q);Q=o(Q);Q=H(Q);return Q;};var h=function(P){P=r(P);P=v(P);P=G(P);P=C(P);P=D(P);P=J(P);P=B(P);P=x(P);P=P.replace(/  +\\n/g," <br />\\n");return P;};var v=function(Q){var P=/(<[a-z\\/!$]("[^"]*"|'[^']*'|[^'">])*>|<!(--.*?--\\s*)+>)/gi;Q=Q.replace(P,function(S){var R=S.replace(/(.)<\\/?code>(?=.)/g,"$1`");R=y(R,"\\\\`*_");return R;});return Q;};var D=function(P){P=P.replace(/(\\[((?:\\[[^\\]]*\\]|[^\\[\\]])*)\\][ ]?(?:\\n[ ]*)?\\[(.*?)\\])()()()()/g,e);P=P.replace(/(\\[((?:\\[[^\\]]*\\]|[^\\[\\]])*)\\]\\([ \\t]*()<?(.*?(?:\\(.*?\\).*?)?)>?[ \\t]*((['"])(.*?)\\6[ \\t]*)?\\))/g,e);P=P.replace(/(\\[([^\\[\\]]+)\\])()()()()()/g,e);return P;};var e=function(V,ab,aa,Z,Y,X,U,T){if(T==undefined){T="";}var S=ab;var Q=aa;var R=Z.toLowerCase();var P=Y;var W=T;if(P==""){if(R==""){R=Q.toLowerCase().replace(/ ?\\n/g," ");}P="#"+R;if(w[R]!=undefined){P=w[R];if(l[R]!=undefined){W=l[R];}}else{if(S.search(/\\(\\s*\\)$/m)>-1){P="";}else{return S;}}}P=y(P,"*_");var ac='<a href="'+P+'"';
if(W!=""){W=W.replace(/"/g,"&quot;");W=y(W,"*_");ac+=' title="'+W+'"';}ac+=">"+Q+"</a>";return ac;};var C=function(P){P=P.replace(/(!\\[(.*?)\\][ ]?(?:\\n[ ]*)?\\[(.*?)\\])()()()()/g,E);P=P.replace(/(!\\[(.*?)\\]\\s?\\([ \\t]*()<?(\\S+?)>?[ \\t]*((['"])(.*?)\\6[ \\t]*)?\\))/g,E);return P;};var E=function(V,ab,aa,Z,Y,X,U,T){var S=ab;var R=aa;var Q=Z.toLowerCase();var P=Y;var W=T;if(!W){W="";}if(P==""){if(Q==""){Q=R.toLowerCase().replace(/ ?\\n/g," ");}P="#"+Q;if(w[Q]!=undefined){P=w[Q];if(l[Q]!=undefined){W=l[Q];}}else{return S;}}R=R.replace(/"/g,"&quot;");P=y(P,"*_");var ac='<img src="'+P+'" alt="'+R+'"';W=W.replace(/"/g,"&quot;");W=y(W,"*_");ac+=' title="'+W+'"';ac+=" />";return ac;};var f=function(Q){Q=Q.replace(/^(.+)[ \\t]*\\n=+[ \\t]*\\n+/gm,function(R,S){return M('<h1 id="'+P(S)+'">'+h(S)+"</h1>");});Q=Q.replace(/^(.+)[ \\t]*\\n-+[ \\t]*\\n+/gm,function(S,R){return M('<h2 id="'+P(R)+'">'+h(R)+"</h2>");});Q=Q.replace(/^(\\#{1,6})[ \\t]*(.+?)[ \\t]*\\#*\\n+/gm,function(R,U,T){var S=U.length;return M("<h"+S+' id="'+P(T)+'">'+h(T)+"</h"+S+">");});function P(R){return R.replace(/[^\\w]/g,"").toLowerCase();}return Q;};var j;var K=function(Q){Q+="~0";var P=/^(([ ]{0,3}([*+-]|\\d+[.])[ \\t]+)[^\\r]+?(~0|\\n{2,}(?=\\S)(?![ \\t]*(?:[*+-]|\\d+[.])[ \\t]+)))/gm;if(z){Q=Q.replace(P,function(S,V,U){var W=V;var T=(U.search(/[*+-]/g)>-1)?"ul":"ol";W=W.replace(/\\n{2,}/g,"\\n\\n\\n");var R=j(W);R=R.replace(/\\s+$/,"");R="<"+T+">"+R+"</"+T+">\\n";return R;});}else{P=/(\\n\\n|^\\n?)(([ ]{0,3}([*+-]|\\d+[.])[ \\t]+)[^\\r]+?(~0|\\n{2,}(?=\\S)(?![ \\t]*(?:[*+-]|\\d+[.])[ \\t]+)))/g;Q=Q.replace(P,function(T,X,V,S){var W=X;var Y=V;var U=(S.search(/[*+-]/g)>-1)?"ul":"ol";var Y=Y.replace(/\\n{2,}/g,"\\n\\n\\n");var R=j(Y);R=W+"<"+U+">\\n"+R+"</"+U+">\\n";return R;});}Q=Q.replace(/~0/,"");return Q;};j=function(P){z++;P=P.replace(/\\n{2,}$/,"\\n");P+="~0";P=P.replace(/(\\n)?(^[ \\t]*)([*+-]|\\d+[.])[ \\t]+([^\\r]+?(\\n{1,2}))(?=\\n*(~0|\\2([*+-]|\\d+[.])[ \\t]+))/gm,function(S,U,T,R,Q){var W=Q;var V=U;var X=T;if(V||(W.search(/\\n{2,}/)>-1)){W=b(u(W));}else{W=K(u(W));
W=W.replace(/\\n$/,"");W=h(W);}return"<li>"+W+"</li>\\n";});P=P.replace(/~0/g,"");z--;return P;};var q=function(P){P+="~0";P=P.replace(/(?:\\n\\n|^)((?:(?:[ ]{4}|\\t).*\\n+)+)(\\n*[ ]{0,3}[^ \\t\\n]|(?=~0))/g,function(Q,S,R){var T=S;var U=R;T=A(u(T));T=I(T);T=T.replace(/^\\n+/g,"");T=T.replace(/\\n+$/g,"");T="<pre><code>"+T+"\\n</code></pre>";return M(T)+U;});P=P.replace(/~0/,"");return P;};var F=function(P){P+="~0";P=P.replace(/(?:^|\\n)```(.*)\\n([\\s\\S]*?)\\n```/g,function(Q,S,R){var U=S;var T=R;T=A(T);T=I(T);T=T.replace(/^\\n+/g,"");T=T.replace(/\\n+$/g,"");T="<pre><code"+(U?' class="'+U+'"':"")+">"+T+"\\n</code></pre>";return M(T);});P=P.replace(/~0/,"");return P;};var M=function(P){P=P.replace(/(^\\n+|\\n+$)/g,"");return"\\n\\n~K"+(a.push(P)-1)+"K\\n\\n";};var r=function(P){P=P.replace(/(^|[^\\\\])(`+)([^\\r]*?[^`])\\2(?!`)/gm,function(S,U,T,R,Q){var V=R;V=V.replace(/^([ \\t]*)/g,"");V=V.replace(/[ \\t]*$/g,"");V=A(V);return U+"<code>"+V+"</code>";});return P;};var A=function(P){P=P.replace(/&/g,"&amp;");P=P.replace(/</g,"&lt;");P=P.replace(/>/g,"&gt;");P=y(P,"*_{}[]\\\\",false);return P;};var x=function(P){P=P.replace(/(\\*\\*|__)(?=\\S)([^\\r]*?\\S[*_]*)\\1/g,"<strong>$2</strong>");P=P.replace(/(\\*|_)(?=\\S)([^\\r]*?\\S)\\1/g,"<em>$2</em>");return P;};var c=function(P){P=P.replace(/((^[ \\t]*>[ \\t]?.+\\n(.+\\n)*\\n*)+)/gm,function(Q,R){var S=R;S=S.replace(/^[ \\t]*>[ \\t]?/gm,"~0");S=S.replace(/~0/g,"");S=S.replace(/^[ \\t]+$/gm,"");S=b(S);S=S.replace(/(^|\\n)/g,"$1  ");S=S.replace(/(\\s*<pre>[^\\r]+?<\\/pre>)/gm,function(T,U){var V=U;V=V.replace(/^  /mg,"~0");V=V.replace(/~0/g,"");return V;});return M("<blockquote>\\n"+S+"\\n</blockquote>");});return P;};var H=function(V){V=V.replace(/^\\n+/g,"");V=V.replace(/\\n+$/g,"");var U=V.split(/\\n{2,}/g);var R=[];var P=U.length;for(var Q=0;Q<P;Q++){var T=U[Q];if(T.search(/~K(\\d+)K/g)>=0){R.push(T);}else{if(T.search(/\\S/)>=0){T=h(T);T=T.replace(/^([ \\t]*)/g,"<p>");T+="</p>";R.push(T);}}}P=R.length;for(var Q=0;Q<P;Q++){while(R[Q].search(/~K(\\d+)K/)>=0){var S=a[RegExp.$1];S=S.replace(/\\$/g,"$$$$");
R[Q]=R[Q].replace(/~K\\d+K/,S);}}return R.join("\\n\\n");};var B=function(P){P=P.replace(/&(?!#?[xX]?(?:[0-9a-fA-F]+|\\w+);)/g,"&amp;");P=P.replace(/<(?![a-z\\/?\\$!])/gi,"&lt;");return P;};var G=function(P){P=P.replace(/\\\\(\\\\)/g,t);P=P.replace(/\\\\([`*_{}\\[\\]()>#+-.!])/g,t);return P;};var J=function(P){P=P.replace(/<((https?|ftp|dict):[^'">\\s]+)>/gi,'<a href="$1">$1</a>');P=P.replace(/<(?:mailto:)?([-.\\w]+\\@[-a-z0-9]+(\\.[-a-z0-9]+)*\\.[a-z]+)>/gi,function(Q,R){return n(L(R));});return P;};var n=function(Q){var P=[function(R){return"&#"+R.charCodeAt(0)+";";},function(R){return"&#x"+R.charCodeAt(0).toString(16)+";";},function(R){return R;}];Q="mailto:"+Q;Q=Q.replace(/./g,function(R){if(R=="@"){R=P[Math.floor(Math.random()*2)](R);}else{if(R!=":"){var S=Math.random();R=(S>0.9?P[2](R):S>0.45?P[1](R):P[0](R));}}return R;});Q='<a href="'+Q+'">'+Q+"</a>";Q=Q.replace(/">.+:/g,'">');return Q;};var L=function(P){P=P.replace(/~E(\\d+)E/g,function(Q,S){var R=parseInt(S);return String.fromCharCode(R);});return P;};var u=function(P){P=P.replace(/^(\\t|[ ]{1,4})/gm,"~0");P=P.replace(/~0/g,"");return P;};var I=function(P){P=P.replace(/\\t(?=\\t)/g,"    ");P=P.replace(/\\t/g,"~A~B");P=P.replace(/~B(.+?)~A/g,function(Q,T,S){var V=T;var R=4-V.length%4;for(var U=0;U<R;U++){V+=" ";}return V;});P=P.replace(/~A/g,"    ");P=P.replace(/~B/g,"");return P;};var y=function(T,Q,R){var P="(["+Q.replace(/([\\[\\]\\\\])/g,"\\\\$1")+"])";if(R){P="\\\\\\\\"+P;}var S=new RegExp(P,"g");T=T.replace(S,t);return T;};var t=function(P,R){var Q=R.charCodeAt(0);return"~E"+Q+"E";};};if(typeof module!=="undefined"){module.exports=Showdown;}if(typeof define==="function"&&define.amd){define("showdown",function(){return Showdown;});}
"""

t_js = """/*t-js*/
(function(){function c(a){this.t=a}function l(a,b){for(var e=b.split(".");e.length;){if(!(e[0]in a))return!1;a=a[e.shift()]}return a}function d(a,b){return a.replace(h,function(e,a,i,f,c,h,k,m){var f=l(b,f),j="",g;if(!f)return"!"==i?d(c,b):k?d(m,b):"";if(!i)return d(h,b);if("@"==i){e=b._key;a=b._val;for(g in f)f.hasOwnProperty(g)&&(b._key=g,b._val=f[g],j+=d(c,b));b._key=e;b._val=a;return j}}).replace(k,function(a,c,d){return(a=l(b,d))||0===a?"%"==c?(new Option(a)).innerHTML.replace(/"/g,"&quot;"):
a:""})}var h=/\\{\\{(([@!]?)(.+?))\\}\\}(([\\s\\S]+?)(\\{\\{:\\1\\}\\}([\\s\\S]+?))?)\\{\\{\\/\\1\\}\\}/g,k=/\\{\\{([=%])(.+?)\\}\\}/g;c.prototype.render=function(a){return d(this.t,a)};window.t=c})();
/* end t-js*/
"""

wiki_style = """/*wiki*/
.error {
	background-color: #FF9999;
}

#errorMessage {
	position: fixed;
	width: 100%;
}

.col {
	padding: 0 1.5em;
}

.row .row {
	margin: 0 -1.5em;
}

.row:before, .row:after {
	content: "";
	display: table;
}

.row:after {
	clear: both;
}

@media only screen {
	.col {
		float: left;
		width: 100%;

		-webkit-box-sizing: border-box;
		-moz-box-sizing: border-box;
		box-sizing: border-box;
	}
}

.container { max-width: 90em; }

@media only screen and (min-width: 34em) {
	.feature, .info { width: 50%; }
}

@media only screen and (min-width: 54em) {
	.content { width: 66.66%; }
	.sidebar { width: 33.33%; }
	.info    { width: 100%;   }
}

@media only screen and (min-width: 76em) {
	.content { width: 58.33%; } /* 7/12 */
	.sidebar { width: 41.66%; } /* 5/12 */
	.info    { width: 50%;    }
}

body {
	font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
	margin: 0;
}

a {
	color: #06f;
}

.wiki-title {
	font-size: 2.6em;
	color: black;
}

.post-title {
	font-size: 2.4em;
	color: #666633;
}

h1 {
	font-size: 1.8em;
	color: #66A366;
}

h2 {
	font-size: 1.4em;
}

h2, h3, h4 {
	margin-top: 0;
}

h3, h4 {
	margin-bottom: 0.5em;
}

p, ul {
	font-size: 0.8125em;
	line-height: 1.5;
	margin: 0 0 1.5em;
}

code {
	font-size: 1.2727em;
	color: #777;
}

iframe {
	border: 0;
	overflow: hidden;
}

.container {
	margin: 0 auto;
	max-width: 90em;
	padding: 1em 0;
}

.footer {
	padding-top: 1.5em;
}

.desc {
	color: #888;
}

.intro {
	border-bottom: 1px dotted #bbb;
	padding-bottom: 1.5em;
}

.social {
	border-top: 1px dotted #bbb;
	padding-top: 1.5em;
}

/* minor responsive adjustments */

.footer {
	border-top: 1px dotted #aaa;
}
.content {
	border-bottom: 1px dotted #aaa;
	margin-bottom: 1.5em;
}

@media only screen and (min-width: 34em) {
	p, ul {
		font-size: 0.875em;
	}
	.feature:first-child,
	.info:first-child {
		border-right: 1px dotted #aaa;
	}
	.container {
		padding: 1em;
	}
	h1 {
		font-size: 2.2em;
	}
	h2 {
		font-size: 1.4em;
	}
}

@media only screen and (min-width: 54em) {
	.content {
		border: none;
		border-right: 1px dotted #aaa;
		margin-bottom: 0;
	}
	.info:first-child {
		border: none;
	}
	h1 {
		font-size: 1.8em;
	}
	h2 {
		font-size: 1.2em;
	}
}

@media only screen and (min-width: 76em) {
	.info:first-child {
		border-right: 1px dotted #aaa;
	}
	h1 {
		font-size: 1.8em;
	}
	h2 {
		font-size: 1.2em;
	}
}

ul.post-cmd-list {
	list-style-type: none;
	float: right;
}

ul.post-cmd-list li{
	display: inline;
}

input {
	width: 100%;
}

textarea {
	width: 100%;
}

pre {
	white-space: pre-wrap;
	background-color: #FFC;
}
"""

wiki_html = """<!DOCTYPE html5>
<html>
<head>
<link href="data:image/x-icon;base64,AAABAAEAEBAAAAAAAABoBQAAFgAAACgAAAAQAAAAIAAAAAEACAAAAAAAAAEAAAAAAAAAAAAAAAEAAAAAAAD+/f4ASLMwAEq0LgBJszAAS7MwAFjezAD7/f0ASqgrAIvOfQBItC0ASbMvAEqzLwBKsjEA////AESMGQD9/fwASbMuAEiyMADj8uEASrMuAEmyMABLsjAALy4wAP7//gBDjBgATbQyAEmyLwBKsi8AcsNgAFfdywBGoicAWN3LAG7AWADH574AzOfFAHp7ewBKtDEAT7UvAEepLAD+/v4A+/z7AEenKQBJtDAARZchAEqrLgD7/PoATrYyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDRIKKg0NDQ0NDQEDIg0NDQ0XAwMFHQUdBR0DAyANDQ0NDS0DHQUFBQUfAygNDQ0NDScOKwoFHQUdAQMDDQ0NDQ0VGAQDAxMQAwMsAxkNDQ0NAwMDAwMUGgMDAwMDDQ0NJwMRAx4DAwMLCgMUAycNDScDAxgDAwMDAyYpGAMPDQ0NDQMDJCQDAwMDAwcNDQ0NDQ0JDRsDAwMDAA0cDQ0NDQ0NDRYGAwMDAyMnAg0NDQ0NDQghLg0NDScMJScNDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" rel="icon" type="image/x-icon" />
<style>
{{!style}}
</style>
</head>
<body>
<div class="container">
	<div id="errorMessage" class="error"></div>
	<div class="row">
		<div class="col content">
			<a href="/"><h1 class='wiki-title'>Wiki</h1></a>
			<div id="postsContainer"></div>
		</div>
		<div class="col sidebar">
			<div>
				<button id="addPost">Add post</button>
			</div>
			<div>
				<form id="formSearch">
					<input id="q" type="text" placeholder="search" name="q"/>
					<button type="submit">Search</button>
					<button type="reset">Reset</button>
				</form>
				<div>
					<ul id="postsMenu">
					</ul>
				</div>
				<button id="more" type="button">More</button>
			</div>
		</div>
	</div>
</div>
<script type="t/template" id="postTmpl">
{{!t_post_tmpl}}
</script>
<script type="t/template" id="postEditTmpl">
{{!t_post_edit_tmpl}}
</script>
<script type="t/template" id="postMenuListTmpl">
{{!t_post_menu_list_tmpl}}
</script>
%for s in scripts:
<script>
{{!s}}
</script>
%end
</body>
</html>
"""

t_post_tmpl ="""<!--Wiki post-->
<div class="post-head" >
	<ul class="post-cmd-list">
		<li><a href="#" class="post-delete">delete</a></li>
		<li><a href="#" class="post-edit">edit</a></li>
		<li><a href="#" class="post-close">close</a></li>
		<li><a href="#" class="post-close-other">close others</a></li>
	</ul>
	<h1 class='post-title'>{{=title}}</h1>
</div>
<div class="post-body">
	{{=body}}
</div>
<ul class="post-cmd-list">
	{{@tags}}
	<li class="tag-link">{{=_val}}</li>
	{{/@tags}}
</ul>
"""

t_post_edit_tmpl = """<!--Edit post form-->
<form class="form-post-edit">
	<legend>Add/Edit Post</legend>
	<input type="hidden" name="isNew" value="{{=isNew}}" class="input-post-new"/>
	<input type="hidden" name="post_id" value="{{=post_id}}" class="input-post-id"/>
	<div>
		<input type="text" name="title" value="{{=title}}" class="input-post-title"/>
	</div>
	<div>
		<textarea name="body" rows="30" cols="100" class="editor">{{=body}}</textarea>
	</div>
	<div>
		<input type="text" name="tags" value="{{=tags}}" class="input-post-tags"/>
	</div>
	<div>
		<button type="submit">Save</button>
		<button type="button" class="form-cancel">Cancel</button>
	</div>
</form>
"""

t_post_menu_list_tmpl = """<li class="wiki-link" data-id="{{=post_id}}" {{ratio}} style="color:green;" {{/ratio}}>{{=title}}</li>"""

app_js = """/*app*/
var wikiUrl = 'http://localhost:8088', errorTimeout = null;

marked.setOptions({
  renderer: new marked.Renderer(),
  gfm: true,
  tables: true,
  breaks: false,
  pedantic: false,
  sanitize: true,
  smartLists: true,
  smartypants: false
});

function ajax(method, url, data, success) {
	var xhReq = new XMLHttpRequest();
	xhReq.open(method, url, true);
	xhReq.onload = success;
	xhReq.onerror = function(e) {
		clearTimeout(errorTimeout);
		var msg = document.getElementById('errorMessage');
		msg.innerHTML = '' + new Date().toString() + 'Error contacting wiki: ' + e;
		errorTimeout = setTimeout(function(){ msg.innerHTML = '' }, 3000);
	};

	if(data) {
		xhReq.setRequestHeader('Content-Type', 'application/json');
		xhReq.send(JSON.stringify(data));
	} else {
		xhReq.send();
	}
};


function closest(selector, elem) {
	var parent = elem.parentNode,
		ancestor = elem.parentNode.parentNode;

	if(!parent || !ancestor) {
		return undefined;
	}

	var res = Array.prototype.slice.call(ancestor.querySelectorAll(selector)),
		found = null;

	res.forEach(function(n){
		if (n === parent) {
			found = n;
			return;
		}
	});

	if(found) {
		return found;
	}

	return closest(selector, parent);
}

var nodeListToArray = function(obj) {
  return [].map.call(obj, function(element) {
    return element;
  })
};

var box = document.querySelectorAll('div');


function loadPosts(q, append) {
	var query = q ? encodeURIComponent(q) : q,
		limit = 20,
		offset = document.getElementById('postsMenu').children.length;

	ajax('GET', wikiUrl + '/search?q=' + query + '&limit=' + limit + '&offset=' + offset, null, function(e) {
		var resp = this.responseText,
			result = JSON.parse(resp);

		if ( result.matches) {
			var cont = document.getElementById('postsMenu'),
				tmpl = new t(document.getElementById('postMenuListTmpl').innerHTML),
				postsHtml = '';

			result.matches.forEach(function(post) {
				postsHtml += tmpl.render(post);
			});

			var contTmp = document.createElement('ul');
			contTmp.innerHTML = postsHtml;

			if(!append) {
				cont.innerHTML = '';
				nodeListToArray(contTmp.querySelectorAll('li')).forEach(function(val) {
					cont.appendChild(val);
				});
			} else {
				nodeListToArray(contTmp.querySelectorAll('li')).forEach( function(val) {
					cont.appendChild(val);
				});
			}
		}
	});
}

function loadPost(post) {
	post.body = marked(post.body);
	var tmpl = new t(document.getElementById('postTmpl').innerHTML);
	var cont = document.createElement('div');
	cont.id = '!/posts/' + post.slug;
	cont.dataset.id = post.slug;
	cont.className = 'wiki-post';
	cont.innerHTML = tmpl.render(post);
	var mainCont = document.getElementById('postsContainer');
	mainCont.insertBefore(cont, mainCont.childNodes[0]);
	window.scrollTo(0, 0);
}

(function() {

	function onEvent(type, selector, callback) {
		var listener = function(ev) {
			var nodeList = document.querySelectorAll(selector);

			Array.prototype.slice.call(nodeList).forEach(function(el) {
				if(el == ev.target) {
					callback.call(ev.target, ev);
				}
			});
		};

		document.addEventListener(type, listener, true);
	};

	onEvent('keydown', '.editor', function(e) {
		var keyCode = e.keyCode || e.which;

		if (keyCode == 190) {  //char '>'
			var start = this.selectionStart, end = this.selectionEnd;
			if (start == end) {
				return;
			}

			e.preventDefault();

			var seltext = this.value.substring(start, end),
				lines = seltext.split('\\n'),
				res = '';

			for(var i = 0; i< lines.length; i++) {
				if (lines[i]) {
					res += '  ' + lines[i] + '\\n';
				}
			}

			this.value = this.value.substring(0, start) + res + this.value.substring(end);
			this.selectionStart = start;
			this.selectionEnd = res.length;
		} else if (keyCode == 188) { //char '<'
			var start = this.selectionStart, end = this.selectionEnd;

			if (start == end) {
				return;
			}

			e.preventDefault();

			var seltext = this.value.substring(start, end),
				lines = seltext.split('\\n'),
				res = '';

			for(var i = 0; i< lines.length; i++) {
				if (lines[i].match(/  (.*)/)) {
					res += lines[i].match(/  (.*)/)[1] + '\\n';
				}
			}

			this.value = this.value.substring(0, start) + res + this.value.substring(end);
			this.selectionStart = start;
			this.selectionEnd = res.length;
		}
	});

	onEvent('click', '.wiki-link', function(e) {
		e.preventDefault();
		var title = this.dataset.id;
		if (!document.getElementById('!/posts/' + title)) {
			ajax('GET', wikiUrl + '/posts/' + title, null, function(e) {
				var resp = this.responseText,
					post = JSON.parse(resp);
				window.location.hash = '!/posts/' + post.slug;
				loadPost(post)
			});
		} else {
			window.location.hash = '!/posts/' + title;
		}
	});

	onEvent('click', '.post-delete',  function(e){
		e.preventDefault();
		var post = closest('.wiki-post', this),
			post_id = post.dataset.id,
			res = confirm('Delete post ' + post_id);
		if (res === true) {
			ajax('DELETE', wikiUrl + '/posts/' + post_id, null, function(e) {
				post.parentNode.removeChild(post);
			});
		}
	});

	onEvent('click', '.post-edit',  function(e){
		e.preventDefault();
		var post = closest('.wiki-post', this),
			post_id = post.dataset.id;

		post.setAttribute('style', 'display:none;');

		ajax('GET', wikiUrl + '/posts/' + post_id, null, function(e) {
			var res = JSON.parse(this.responseText);
			var tmpl = new t(document.getElementById('postEditTmpl').innerHTML),
				cont = document.createElement('div'),
				tags = '';

			res.tags.forEach(function(val, idx) {
				tags += val + ',';
			});

			if (tags) {
				tags = tags.substring(0, tags.length - 1);
			}

			cont.className = 'post-edit-form';
			cont.innerHTML = tmpl.render({post_id:post_id, title:res.title, body:res.body, tags: tags.trim(), 'isNew':'0'});
			post.parentNode.insertBefore(cont, post);
		});
	});

	onEvent('click', '#addPost', function(e) {
		e.preventDefault();
		var tmpl = new t(document.getElementById('postEditTmpl').innerHTML),
			form = document.createElement('div')
			cont = document.getElementById('postsContainer');
		form.className = 'post-edit-form';
		form.innerHTML = tmpl.render({title:'', body:'', tags: '', 'isNew':'1'});
		cont.insertBefore(form, cont.childNodes[0]);
	});

	onEvent('submit', '#formSearch', function(e) {
		e.preventDefault();
		var query = document.getElementById('q');

		if(query) {
			loadPosts(query.value);
		}
	});

	onEvent('submit', '.form-post-edit', function(e) {
		e.preventDefault();

		var that = this,
			isNew = that.querySelector('.input-post-new'),
			inputPostId = that.querySelector('.input-post-id'),
			inputTitle = that.querySelector('.input-post-title'),
			inputTags = that.querySelector('.input-post-tags'),
			inputBody = that.querySelector('textarea'),
			data = {title: inputTitle.value, body: inputBody.value, tags: inputTags.value.split(',')},
			url = wikiUrl + '/posts';

		if(inputPostId.value) {
			url = url + '/'+ inputPostId.value;
		}

		var method = isNew.value == '1' ? 'POST' : 'PUT';

		ajax(method, url, data, function(e) {
			var resp = this.responseText,
				post = JSON.parse(resp),
				formCont = that.parentNode;
			formCont.parentNode.removeChild(formCont);
			loadPost(post);
		});
	});

	onEvent('click', '.form-cancel', function(e) {
		e.preventDefault();
		var cont = closest('.post-edit-form', this);
		cont.parentNode.removeChild(cont);
	});

	onEvent('click', '.post-close', function(e) {
		e.preventDefault();
		var cont = closest('.wiki-post', this);
		cont.parentNode.removeChild(cont);
	});

	onEvent('click', '.post-close-other', function(e) {
		e.preventDefault();
		var cont = closest('.wiki-post', this),
			docs = nodeListToArray(document.querySelectorAll('.wiki-post'));

		docs.forEach(function(n) {
			if(n === cont) {
				return;
			}

			n.parentNode.removeChild(n);
		});
	});

	onEvent('click', '#more', function(e) {
		e.preventDefault();
		loadPosts('', true);
	});

	loadPosts('', true);
})();
"""

class folded_unicode(unicode): pass


class literal_unicode(unicode): pass


class Post(object):

	def __init__(self, title, body, created=None, modified=None, tags=[]):
		self.title = str(title).strip()
		self.body = literal_unicode(body.strip())
		self.slug = str(Post.build_slug(self.title))
		self.tags = [t for t in tags if t]
		self.created = str(created) if created else None
		self.modified = str(modified) if modified else None

	def __cmp__(self, other):
		if not other:
			return -1

		return (int(self.created > other.created) or -1) if self.created != other.created else 0

	@staticmethod
	def build_slug(title):
		return re.sub(r'[\.!,;/\?#\ ]+', '-', title).strip().lower()


def folded_unicode_representer(dumper, data):
	return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')

def literal_unicode_representer(dumper, data):
	return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(folded_unicode, folded_unicode_representer)
yaml.add_representer(literal_unicode, literal_unicode_representer)


def load_wiki():
	with file(WIKI_FILE) as f:
		for p in yaml.load_all(f):
			if 'slug' in p:
				del p['slug']
			post = Post(**p)
			wiki[post.slug] = Post(**p)


wiki = {}


class BinderPlugin:

	api = 2

	def apply(self, callback, route_ctx):
		def wrapper(*args, **url_args):
			action_kwargs = {}
			action_kwargs.update(url_args)

			if bottle.request.query:
				action_kwargs.update(bottle.request.query)

			if isinstance(bottle.request.json, dict):
				action_kwargs.update(bottle.request.json)

			return callback(**action_kwargs)

		return wrapper


bottle.install(BinderPlugin())


@get('/')
def index():
	return template(
			wiki_html,
			style=wiki_style,
			scripts=[
				t_js,
				marked_js,
				app_js],
			t_post_tmpl=t_post_tmpl,
			t_post_edit_tmpl = t_post_edit_tmpl,
			t_post_menu_list_tmpl = t_post_menu_list_tmpl)


@get('/posts')
def get_posts(offset=0, limit=10):
	res = [{'title': p.title, 'slug': p.slug, 'created': p.created, 'modified': p.modified} for p in sorted(wiki.values(), reverse=True)]
	return {'posts': res}


@get('/posts/:post_id')
def show_post(post_id):
	temp = copy.copy(wiki[post_id].__dict__)
	return temp


@get('/search')
def search(q=None, limit=20, offset=0):
	limit = int(limit)
	offset = int(offset)
	matches = []

	if not q:
		matches = [{'title': p.title, 'post_id': p.slug} for p in sorted(wiki.values(), reverse=True)]
		matches = matches[offset:offset+limit]

		return {'matches' : matches}

	for post in wiki.values():
		found = difflib.get_close_matches(q, itertools.chain(post.body.split(), post.tags, post.title.split()), cutoff=0.8)
		if found:
			matches.append({'post_id': post.slug,'title' : post.title , 'ratio': 1 if q in found else 0})

	return {'matches' : matches}


@post('/posts')
def create_post(title, body, tags=[]):
	tags = [str(t).strip() for t in tags if t]
	post = wiki.get(Post.build_slug(title))
	if post:
		raise HTTPError(status=409)
	created = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
	post = Post(title=title, body=body, tags=tags, created=created)
	wiki[post.slug] = post
	persist_changes()
	temp = copy.copy(wiki[post.slug].__dict__)
	return temp


@put('/posts/:post_id')
def update_post(post_id, title, body, tags=[]):
	tags = [str(t).strip() for t in tags if t]
	post = wiki.get(post_id)

	if not post:
		raise HTTPError(status=404)

	modified=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
	body_lines = [l.rstrip() for l in body.split('\n')] #to avoid yaml encoding when trailing whispaces

	post = Post(title=title, body='\n'.join(body_lines), tags=tags, created=post.created, modified=modified)

	if post.slug != post_id:
		del wiki[post_id]

	wiki[post.slug] = post
	persist_changes()
	temp = copy.copy(wiki[post.slug].__dict__)
	return temp


@delete('/posts/:post_id')
def delete_post(post_id):
	del wiki[post_id]
	persist_changes()


def persist_changes():
	with file(WIKI_FILE, 'w') as f:
		docs = [p.__dict__ for p in wiki.values()]
		yaml.dump_all(docs, f, explicit_start=True, default_flow_style=False)


if os.name == 'nt':
	import win32serviceutil, win32service, win32event, servicemanager

	class AppServerSvc (win32serviceutil.ServiceFramework):
		_svc_name_ = "WikiService"
		_svc_display_name_ = "Wiki Service"

		def __init__(self,args):
			win32serviceutil.ServiceFramework.__init__(self,args)
			self.hWaitStop = win32event.CreateEvent(None,0,0,None)
			self.running = False
			self.p = None

		def SvcStop(self):
			self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
			win32event.SetEvent(self.hWaitStop)
			self.running = False
			try:
				self.p.terminate()
			except Exception:
				pass
			finally:
				self.p = None

		def SvcDoRun(self):
			servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
					servicemanager.PYS_SERVICE_STARTED,
					(self._svc_name_,''))
			self.main()

		def main(self):
			self.running = True
			while self.running:
				if not self.p:
					self.p = multiprocessing.Process(target=main, args=(False, 'e:\\alex\\Google Drive\\wiki\\wiki_alex.yaml'))
					self.p.start()
				elif self.p.is_alive():
					try:
						time.sleep(1)
					except Exception:
						pass


def run_as_windows_service():
	'''Runs the wiki as a windows service'''
	win32serviceutil.HandleCommandLine(AppServerSvc)


def main(reloader=False, path=None):
	'''Runs the wiki'''
	global WIKI_FILE

	if path:
		WIKI_FILE = path

	logging.debug('%s reading %s' % (os.getpid(), WIKI_FILE))

	try:
		load_wiki()
	except Exception, e:
		logging.error('error %s', e)

	logging.debug('%s loaded wiki' % (os.getpid(),))
	run(host=WIKI_HOST, port=WIKI_PORT, reloader=reloader)


if __name__ == '__main__':
	if os.name == 'nt':
		if len(sys.argv) > 1:
			run_as_windows_service()
		else:
			main()
	else:
		main(reloader=True)

