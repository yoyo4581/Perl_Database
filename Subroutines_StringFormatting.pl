use strict;
use warnings;


sub three_points{

  my $first = shift;
  my $second = shift;
  my $third = shift;

  my %inputs = ( Gene => $first, num_base_pairs => $second, Organism => $third);
  return \%inputs;
}

my $call_1 = three_points("ABC", 350, "An Org");
my $call_2 = three_points("DEF", 500, "DEF Org");
my $call_3 = three_points("GHI", 1000, "Last Org");

my @array1 = ($call_1, $call_2, $call_3); 


foreach my $element (@array1){
  print("----\n");
  foreach my $key (keys %$element){
     my $value = %$element{$key};
     print($key." => ".$value."\n");
  }
}

