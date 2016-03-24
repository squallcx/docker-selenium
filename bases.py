import hashlib, re, time, datetime, os, copy, dateparser, locale, traceback, shutil

from ctools.setup import settings
from errors import StatusError

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from weasyprint import HTML, CSS

import subprocess

class Selenium():
	def __init__(self, provider, tid, ctx, options, fs, meta_collection):
		locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

		self.provider = provider
		self.tid = tid
		self.ctx = ctx
		self.options = options
		self.fs = fs
		self.mc = meta_collection
		self.exported_files = list()

		self.display = Display(visible=0, size=(800, 600))
		self.display.start()

		pref = Options()
		
		dl_path = settings.config.get('download', 'directory')
		self.dl_dir = os.path.join(dl_path, tid)
		os.makedirs(self.dl_dir, exist_ok=True)

		profile = {
			'download.default_directory': self.dl_dir,
			'download.prompt_for_download' : False,
			'download.directory_upgrade': True,
			'plugins.plugins_disabled': ["Chrome PDF Viewer"]
		}
		pref.add_experimental_option('prefs', profile)
		pref.add_argument('--disable-extensions')
		pref.add_argument('--no-sandbox')

		self.browser = webdriver.Chrome(chrome_options=pref )
		self.browser.set_page_load_timeout(options['timeout'])

	def close(self):
		try:
			self.browser.quit()
		except:
			settings.logger.debug('failed to quit browser, killing')
			subprocess.call(["pkill", "-9", "chromedriver"])
		self.display.stop()

	def run(self, meta):
		self.metadata = []
		self.ancestry = []
		self.history = []
		self.metadata.append(
			{
				'pid': self.provider['id'],
				'tid': self.tid,
				'rid': 'testing',

				'type': self.options['type'],
				'method': 'download'
			}
		)

		self._steps(meta['steps'])
		self.close()

	# TOOLS

	def _checksum(self, filename):
		h = hashlib.md5()
		with open(filename, 'rb') as fd:
			for chunk in iter(lambda: fd.read(4096), b""):
				h.update(chunk)
		return h.hexdigest()

	def _merge(self, dictlist):
		result = copy.copy(dictlist[0])
		for d in dictlist[1:]:
			result.update(d)
		return result

	def _get(self, element):
		if 'relative' in element and element['relative'] == True:
			base = self.ancestry[-1]
		else: base = self.browser

		if element['type'] == 'xpath':
			elem = base.find_element_by_xpath(element['value'])
		elif element['type'] == 'css':
			elem = base.find_element_by_css_selector(element['value'])
		return elem

	def _get_many(self, elements):
		if 'relative' in elements and elements['relative'] == 'true':
			base = self.ancestry[-1]
		else: base = self.browser

		if elements['type'] == 'xpath':
			elems = base.find_elements_by_xpath(elements['value'])
		elif elements['type'] == 'css':
			elems = base.find_elements_by_css_selector(elements['value'])
		return elems

	def _export(self, filename):
		fullname = os.path.join(self.dl_dir, filename)

		self.metadata.append(
			{
				'did': self._checksum(fullname),
				'collected': datetime.datetime.now(),
				'size': os.path.getsize(fullname),
				'name': filename
			}
		)
		local_metadata = self._merge(self.metadata)
		self.metadata.pop()
		if not self.fs.find_one({'did': local_metadata['did']}):
			self.fs.put(open(fullname, 'rb'), did=local_metadata['did'])
			self.mc.insert_one(copy.copy(local_metadata))
			self.exported_files.append(local_metadata)
		os.remove(fullname)

	def _current_already_collected(self):
		return bool(self.mc.find_one({"num": self._merge(self.metadata)["num"]}))

	# ENGINE

	def _sleep(self, seconds):
		time.sleep(seconds)

	def _raise(self, status):
		raise StatusError(status)

	def _download(self, element):
		if self._current_already_collected(): return

		content = os.listdir(self.dl_dir)
		cu = self.browser.current_url
		self._click(element)
		if self.browser.current_url != cu:
			self._back(iterations=1)
			return
			
		stime = time.time()
		while len(content) == len([e for e in os.listdir(self.dl_dir) if not e.endswith('.crdownload') and not e.startswith('.')]):
			if time.time() - stime > float(settings.config.get('download', 'timeout')):
				self._raise('TIMEOUT')
			time.sleep(0.2)

		filename = (set(os.listdir(self.dl_dir)) - set(content)).pop()

		self._export(filename)

	def _generate(self, element):
		if self._current_already_collected(): return

		content = self.browser.execute_script('return document.body.parentNode.innerHTML')
		tmpname = 'generated_invoice.pdf'
		fullname = os.path.join(self.dl_dir, tmpname)
		try:
			HTML(string=content).write_pdf(fullname,  stylesheets=[CSS(string='''
				body {
 					 width: 210mm
				}
				'''
			)])
		except Exception:
			pass
		else:
			self.metadata.append({'method': 'generate'})
			self._export(tmpname)
			self.metadata.pop()

	def _back(self, iterations):
		for i in range(iterations):
			self.browser.back()

	def _click(self, element):
		self._get(element).click()

	def _navigate(self, url):
		self.history.append(self.browser.current_url)
		self.browser.get(url)

	def _input(self, element, tag):
		self._get(element).send_keys(self.ctx[tag])

	def _metadata(self, **args):
		data = {}
		for name, desc in args.items():
			elem = self._get(desc['element'])

			expression = desc['regexp'].encode()
			string = elem.text.strip().encode()

			m = re.compile(expression).search(string)
			result = m.group(1) if m else None
			#if name == 'amount':
			#	data[name] = locale.atof(result.decode())
			if name == 'date':
				data[name] = dateparser.parse(result.decode())
			else:
				data[name] = result
		self.metadata.append(data)
		print(data)
	
	def _foreach(self, elements, steps, skip=None):
		elems = self._get_many(elements)
		lm = len(self.metadata)

		for i, elem in enumerate(elems):
			if skip != None and i < skip:
				continue
			self.ancestry.append(elem)
			try:
				self._steps(steps)
			except StaleElementReferenceException:
				self._foreach(elements, steps, i)
				break
			finally:
				self.ancestry.pop()
				self.metadata = self.metadata[:lm]

	def _pagination(self, element, steps):
		while True:
			self._steps(steps)
			try:
				self._get(element).click()
			except NoSuchElementException:
				break

	def _select(self, element, steps):
		index = 0
		while True:
			select = Select(self._get(element))
			if not (index < len(select.options)):
				break
			select.select_by_index(index)
			self._steps(steps)
			index += 1

	def _exists(self, element):
		try:
			self._get(element)
		except NoSuchElementException:
			return False
		else:
			return True

	def _equal(self, element, expression, tag='text'):
		if not self._exists(element):
			return False

		content = self._get(element).text.strip().encode() if tag == 'text' else self._get(element).get_attribute(tag).encode()
		regexp = re.compile(expression.encode())
		return bool(regexp.search(content))

	def _if(self, condition, _then, _else = []):
		if self._step(condition):
			self._steps(_then)
		else:
			self._steps(_else)
		
	def _step(self, step):
		for functor, args in step.items():
			return getattr(self, '_' + functor)(**args)

	def _steps(self, steps):
		for step in steps:
			self._step(step)
