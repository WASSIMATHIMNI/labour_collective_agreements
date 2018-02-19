//Create user schema using passportlocalmongoose
const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const Filedata = new Schema({
  agreementnumber : String,
  effectivedate : String,
  expirydate : String,
  settlementdate : String,
  jurprov : String,
  jurisdictioncode : String,
  employeecount : String,
  naicscodeid_firsttwodigit : String,
  publicprivate : String,
  naicscodeid : String,
  summaryreportavailabilityindicator : String,
  province : String,
  provinceenglish : String,
  provincefrench : String,
  citynameenglish : String,
  citynamefrench : String,
  cityprovincenameenglish : String,
  cityprovincenamefrench : String,
  unionid : String,
  unionnameenglish : String,
  unionnamefrench : String,
  affiliationtext : String,
  unionacronymenglish : String,
  unionacronymfrench : String,
  noccodeid : String,
  name_e : String,
  name_f : String,
  companyofficialnameeng : String,
  companyofficialnamefra : String,
  currentagreementindicator: String
});

module.exports = mongoose.model('Filedata', Filedata);