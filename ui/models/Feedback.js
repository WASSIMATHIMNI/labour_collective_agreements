//Create user schema using passportlocalmongoose
const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const Feedback = new Schema({
  raw_passage : String,
  metadata : String,
  pdf_url : String,
  feedback : Boolean,
  query : String,
  date : Date
});

module.exports = mongoose.model('Feedback', Feedback);