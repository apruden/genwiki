/*app*/
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
