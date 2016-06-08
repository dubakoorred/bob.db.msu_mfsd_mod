#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Ivana Chingovska <ivana.chingovska@idiap.ch>
#Mon 16 Mar 15:27:28 CET 2015
#
# Copyright (C) 2011-2012 Idiap Research Institute, Martigny, Switzerland
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""A few checks at the MSU MFSD database.
"""

import os, sys
import unittest
import pkg_resources
from . import Database, File
from nose.plugins.skip import SkipTest
import bob.io.base
import bob.io.video
import bob.io.image
import bob.db.base
import numpy as np

class MFSDDatabaseTest(unittest.TestCase):
  """Performs various tests on the MSU_MFSD spoofing attack database."""
  
  
  
  def test02_dumplist(self):
    from bob.db.base.script.dbmanage import main
    self.assertEqual(main('msu_mfsd_mod dumplist --self-test'.split()), 0)

  def test03_checkfiles(self):
    from bob.db.base.script.dbmanage import main
    self.assertEqual(main('msu_mfsd_mod checkfiles --self-test'.split()), 0)
  
  def test04_manage_files(self):

    from bob.db.base.script.dbmanage import main

    self.assertEqual(main('msu_mfsd_mod files'.split()), 0)

  def test05_query_obj(self):
    db = Database()
    
    fobj = db.objects()
    self.assertEqual(len(fobj), 280) # number of all the videos in the database

    fobj = db.objects(fold_no=1)
    self.assertEqual(len(fobj), 280) # number of all the videos in the database

    fobj = db.objects(groups='train', ids=['01'])
    self.assertEqual(len(fobj), 0) # number of train videos for client '01' (fold 0)
       
    fobj = db.objects(groups='test', ids=['01'])
    self.assertEqual(len(fobj), 8) # number of train videos for client '01' (fold 0)

    fobj = db.objects(groups='devel', ids=['01'], fold_no=1)
    self.assertEqual(len(fobj), 8) # number of devel videos for client '01' (fold 1)
     
    fobj = db.objects(groups='devel', ids=['55'], fold_no=1)
    self.assertEqual(len(fobj), 0) # number of devel videos for client '55' (fold 1)
    
    fobj = db.objects(groups='train', fold_no=1, cls='real')
    self.assertEqual(len(fobj), 20) # number of real train videos

    fobj = db.objects(groups='devel', fold_no=1, cls='attack')
    self.assertEqual(len(fobj), 60) # number of attack devel videos

    fobj = db.objects(groups='train', fold_no=1, cls='attack', types='video_mobile')
    self.assertEqual(len(fobj), 20) # number of video_mobile attack devel videos

    fobj = db.objects(groups='test', fold_no=1, cls='attack', types='print', qualities='mobile')
    self.assertEqual(len(fobj), 15) # number of print attack test videos recorded with mobile

    filename = os.path.join('real', 'real_client001_android_SD_scene01')
    thisobj = File(filename, 'real', 'test')
    self.assertEqual(thisobj.get_client_id(), '01')
    self.assertEqual(thisobj.get_type(), None)
    self.assertEqual(thisobj.get_quality(), 'mobile')

    self.assertEqual(thisobj.videofile('xxx'), 'xxx/real/real_client001_android_SD_scene01.mp4')
    self.assertTrue(thisobj.is_real())

    filename = os.path.join('attack', 'attack_client003_laptop_SD_ipad_video_scene01')
    thisobj = File(filename, 'attack', 'test')
    self.assertEqual(thisobj.get_client_id(), '03')
    self.assertEqual(thisobj.get_type(), 'video_hd')
    self.assertEqual(thisobj.get_quality(), 'laptop')

    self.assertEqual(thisobj.make_path('xxx','.mov'), 'xxx/attack/attack_client003_laptop_SD_ipad_video_scene01.mov')
    self.assertEqual(thisobj.videofile('xxx'), 'xxx/attack/attack_client003_laptop_SD_ipad_video_scene01.mov')
    self.assertFalse(thisobj.is_real())
        
  def test06_check_rotation(self):
    filename = os.path.join('real', 'real_client003_android_SD_scene01')
    thisobj = File(filename, 'real', 'test')
    self.assertTrue(thisobj.is_rotated())

    filename = os.path.join('attack', 'attack_client003_laptop_SD_ipad_video_scene01')
    thisobj = File(filename, 'attack', 'test')
    self.assertFalse(thisobj.is_rotated())

  def test07_check_flip_on_load(self):
#       dbfolder = 'bob/db/msu_mfsd_mod/test_images/'  #simulated db repo. containing only the 2 videos used in this test.
#      dbfolder = pkg_resources.resource_filename('bob.db.msu_mfsd_mod','test_images')
      dbfolder = pkg_resources.resource_filename(__name__ , 'test_images')
      flipped_file = 'real_client005_android_SD_scene01'
      upright_file = 'real_client005_laptop_SD_scene01'
      #make sure the dbfolder and all files necessary exist.
      self.assertTrue(os.path.isdir(dbfolder))
      self.assertTrue(os.path.exists(os.path.join(dbfolder, 'real_client005_android_SD_scene01_frame0_correct.hdf5')))
      self.assertTrue(os.path.exists(os.path.join(dbfolder, 'real_client005_laptop_SD_scene01_frame0_correct.hdf5')))
      self.assertTrue(os.path.exists(os.path.join(dbfolder, 'real/real_client005_android_SD_scene01.mp4')))
      self.assertTrue(os.path.exists(os.path.join(dbfolder, 'real/real_client005_laptop_SD_scene01.mov')))

      #test the 'rotated' file is correctly presented.
      file1 = os.path.join('real', flipped_file)
      thisobj = File(file1, 'real','test') 
      vin = thisobj.load(dbfolder)
      firstframe = vin[0]
      hf = bob.io.base.HDF5File(os.path.join(dbfolder, 'real_client005_android_SD_scene01_frame0_correct.hdf5'), 'r')
      reference_frame1 = hf.read('color_frame')
      difsum1  = np.sum(np.fabs(firstframe - reference_frame1))
#        print 'flipped video: SAD:', difsum1
      self.assertTrue(np.array_equal(firstframe, reference_frame1))
      #
#       # test that 'not_rotated' files are also correctly presented.
#THIS TEST IS SUPPRESSED FOR NOW BECAUSE IT DOESNOT RUN ON TRAVIS CORRECTLY.
#       file2= os.path.join('real', upright_file)
#       thisobj = File(file2, 'real','test') 
#       vin = thisobj.load(dbfolder)
#       firstframe = vin[0]
#       hf = bob.io.base.HDF5File(os.path.join(dbfolder, 'real_client005_laptop_SD_scene01_frame0_correct.hdf5'), 'r')
#       reference_frame = hf.read('color_frame')
#       difsum2  = np.sum(np.fabs(firstframe - reference_frame))
#       print 'upright video: SAD:', difsum2 #returns Inf on travis, but 0 (as it should be) on my machine.
#       self.assertTrue(np.array_equal(firstframe, reference_frame))


