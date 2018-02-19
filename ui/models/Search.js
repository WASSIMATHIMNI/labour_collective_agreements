//Create user schema using passportlocalmongoose
const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const Search = new Schema({
  searchStr: String,
  selectedNum : Number
});

module.exports = mongoose.model('Search', Search);