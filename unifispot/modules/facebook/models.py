import arrow
from wtforms import BooleanField,TextField,IntegerField

from unifispot.core.db import db,FORMAT_DATETIME,JSONEncodedDict
from unifispot.core.const import *
from unifispot.core.models import Loginauth,Wifisite
from unifispot.utils.modelhelpers import SerializerMixin,CRUDMixin,LoginconfigMixin
from unifispot.utils.translation import format_datetime



class Fbconfig(LoginconfigMixin,CRUDMixin,SerializerMixin,db.Model): 
    id                  = db.Column(db.Integer, primary_key=True)
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))
    siteid              = db.Column(db.Integer, db.ForeignKey('wifisite.id'))     
    auth_fb_like        = db.Column(db.Integer,default=FACEBOOK_LIKE_OFF)
    auth_fb_post        = db.Column(db.Integer,default=FACEBOOK_POST_OFF)
    fb_appid            = db.Column(db.String(200))
    fb_app_secret       = db.Column(db.String(200))
    fb_page             = db.Column(db.Text,default='https://www.facebook.com/Unifispot-1652553388349756')    
    data_limit          = db.Column(db.BigInteger,default=0)
    time_limit          = db.Column(db.Integer,default=60)    
    speed_ul            = db.Column(db.Integer,default=0)    
    speed_dl            = db.Column(db.Integer,default=0)    
    session_limit_control= db.Column(db.Integer)
    session_overridepass = db.Column(db.String(50)) 
    relogin_policy      = db.Column(db.String(25),default='onetime')
    optinout_fields     = db.Column(JSONEncodedDict(255))  
    fbprofile_fields    = db.Column(JSONEncodedDict(255))    
    site                = db.relationship(Wifisite, backref=db.backref("fbconfigs", \
                                cascade="all,delete"))    
   
    #serializer arguement
    __json_hidden__ = []

    json_modifiers__ = {'optinout_fields':'modeljson_to_dict',
                          'fbprofile_fields':'modeljson_to_dict',}

    __form_fields_avoid__ = ['id','siteid','account_id']

    __form_fields_modifiers__ =  { 'optinout_fields':'form_to_modeljson',
                                   'fbprofile_fields':'form_to_modeljson'}

    def optinout_enabled(self):
        if self.optinout_fields and self.optinout_fields.get('optinout_enable'):
            return 1 
        else:
            return 0


    def get_extra_profile_fields(self):
        '''return extra fields to be collected from facebook user

            should return a string of permissions seperated by comma

            https://developers.facebook.com/docs/facebook-login/permissions#reference-user_location

        '''
        fields = []
        fbprofile_fields = self.fbprofile_fields or {}

        if fbprofile_fields.get('fbprofile_birthday'):
            fields.append('user_birthday')

        if fbprofile_fields.get('fbprofile_location'):
            fields.append('user_location')
            
        if fields:
            return ','.join(fields)
        else:
            return ''


class Fbauth(Loginauth):
    fbprofileid     = db.Column(db.String(200),index=True) 
    fbtoken         = db.Column(db.Text)   
    fbliked         = db.Column(db.Integer,default=0,index=True)
    fbcheckedin     = db.Column(db.Integer,default=0,index=True)
    __mapper_args__ = {'polymorphic_identity': 'fbauth'} 

    def reset_lastlogin(self):
        self.last_login_at = arrow.utcnow().naive
        self.fbcheckedin = 0
        self.save()

    def login_completed(self,loginconfig):
        if self.state == LOGINAUTH_INIT:
            return False
        elif loginconfig.auth_fb_like and not self.fbliked:
            return False
        elif loginconfig.auth_fb_post and not self.fbcheckedin:
            return False 
        else:
            return True