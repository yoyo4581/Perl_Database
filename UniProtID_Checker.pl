use strict;
use warnings;
use autodie;

my $filename = "./Resources/test_id.txt";
open(my $fh, '<:encoding(UTF-8)', $filename) or die "Could not open '$filename' $!";
open(my $oh, '>:encoding(UTF-8)', "./HW_1_output.txt");

sub Check{

  my $string =  $_[0];
  if ($string =~ /^[a-zA-Z]{2}\d{4,5}/){
     print {$oh} $string."\n";
  }
  else{
     print("Error invalid string ".$string."\n");
  }
}


while (my $row = <$fh>) {
  $row =~ s/^\s+|\s+$//g;
  Check($row);
}  
close $fh;
close $oh;
